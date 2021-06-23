from odoo import models, fields, api, _
from odoo.exceptions import Warning,UserError
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import *

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_no = fields.Char("Tax Number", copy=False)
    tax_date = fields.Date('Tax Date', copy=False)

    @api.depends('move_id.line_ids', 'move_id.line_ids.tax_line_id', 'move_id.line_ids.debit', 'move_id.line_ids.credit')
    def _compute_tax_base_amount(self):
        for move_line in self:
            if move_line.tax_line_id:
                base_lines = move_line.move_id.line_ids.filtered(lambda line: move_line.tax_line_id in line.tax_ids)
                if base_lines:
                    move_line.tax_base_amount = abs(sum(base_lines.mapped('balance')))
                else:
                    tax = move_line.payment_id.payment_line_ids.filtered(lambda line: line.invoice_id == move_line.invoice_id) \
                            .tax_line_ids.filtered(lambda tax: tax.tax_id == move_line.tax_line_id)
                    move_line.tax_base_amount = tax.base_amt
            else:
                move_line.tax_base_amount = 0

    def auto_reconcile_lines_payment_journal(self, payment_journal):
        if not self.ids:
            return self
        sm_debit_move, sm_credit_move = self._get_pair_to_reconcile()
        #there is no more pair to reconcile so return what move_line are left
        if not sm_credit_move or not sm_debit_move:
            return self
        company_currency_id = self[0].account_id.company_id.currency_id
        account_curreny_id = self[0].account_id.currency_id
        field = (account_curreny_id and company_currency_id != account_curreny_id) and 'amount_residual_currency' or 'amount_residual'
        if not sm_debit_move.debit and not sm_debit_move.credit:
            #both debit and credit field are 0, consider the amount_residual_currency field because it's an exchange difference entry
            field = 'amount_residual_currency'
        if self[0].currency_id and all([x.currency_id == self[0].currency_id for x in self]):
            #all the lines have the same currency, so we consider the amount_residual_currency field
            field = 'amount_residual_currency'
        if self._context.get('skip_full_reconcile_check') == 'amount_currency_excluded':
            field = 'amount_residual'
        elif self._context.get('skip_full_reconcile_check') == 'amount_currency_only':
            field = 'amount_residual_currency'

        amount_reconcile_currency = 0.0
        for pay_line in payment_journal.line_ids:
            writeoff_amt = pay_line.settle_full_invoice and pay_line.variance_amt
            if pay_line.invoice_id == sm_debit_move.mapped('invoice_id'):
                amount_reconcile = pay_line.paying_amt + writeoff_amt
                if amount_reconcile >= sm_debit_move[field] or amount_reconcile < -sm_credit_move[field]:
                    self -= sm_debit_move
                else:
                    self -= sm_credit_move
                break
            elif pay_line.invoice_id == sm_credit_move.mapped('invoice_id'):
                if field == 'amount_residual':
                    amount_reconcile = pay_line.paying_amt + writeoff_amt
                    if amount_reconcile >= -sm_credit_move[field] or amount_reconcile < sm_debit_move[field]:
                        self -= sm_credit_move
                    else:
                        self -= sm_debit_move
                    break
                else:
                    amount_reconcile_currency = pay_line.paying_amt + writeoff_amt
                    amount_reconcile = payment_journal.currency_id.with_context(
                        date=payment_journal.payment_date).compute(amount_reconcile_currency, company_currency_id)
                    self -= sm_credit_move
                    if amount_reconcile_currency == sm_debit_move[field]:
                        self -= sm_debit_move
                    break
        currency = False
        if sm_debit_move.currency_id == sm_credit_move.currency_id and sm_debit_move.currency_id.id:
            currency = sm_credit_move.currency_id.id
            amount_reconcile_currency = min(sm_debit_move.amount_residual_currency, -sm_credit_move.amount_residual_currency, amount_reconcile_currency)
        amount_reconcile = min(sm_debit_move.amount_residual, -sm_credit_move.amount_residual, amount_reconcile)

        if self._context.get('skip_full_reconcile_check') == 'amount_currency_excluded':
            amount_reconcile_currency = 0.0

        self.env['account.partial.reconcile'].create({
            'debit_move_id': sm_debit_move.id,
            'credit_move_id': sm_credit_move.id,
            'amount': amount_reconcile,
            'amount_currency': amount_reconcile_currency,
            'currency_id': currency,
        })

        #Iterate process again on self
        return self.auto_reconcile_lines_payment_journal(payment_journal)

    @api.multi
    def reconcile_payment_journal(self, payment_journal): #, writeoff_acc_id=False, writeoff_journal_id=False):
        # Empty self can happen if the user tries to reconcile entries which are already reconciled.
        # The calling method might have filtered out reconciled lines.
        if not self:
            return True

        #Perform all checks on lines
        company_ids = set()
        all_accounts = []
        partners = set()
        for line in self:
            company_ids.add(line.company_id.id)
            all_accounts.append(line.account_id)
            if (line.account_id.internal_type in ('receivable', 'payable')):
                partners.add(line.partner_id.id)
            if (line.matched_debit_ids or line.matched_credit_ids) and line.reconciled:
                raise UserError(_('You are trying to reconcile some entries that are already reconciled!'))
        if len(company_ids) > 1:
            raise UserError(_('To reconcile the entries company should be the same for all entries!'))
        if len(set(all_accounts)) > 1:
            raise UserError(_('Entries are not of the same account!'))
        if not (all_accounts[0].reconcile or all_accounts[0].internal_type == 'liquidity'):
            raise UserError(_('The account %s (%s) is not marked as reconciliable !') % (all_accounts[0].name, all_accounts[0].code))

        #reconcile everything that can be
        remaining_moves = self.auto_reconcile_lines_payment_journal(payment_journal)

        #if writeoff_acc_id specified, then create write-off move with value the remaining amount from move in self
        # if writeoff_acc_id and writeoff_journal_id and remaining_moves:
        #     all_aml_share_same_currency = all([x.currency_id == self[0].currency_id for x in self])
        #     writeoff_vals = {
        #         'account_id': writeoff_acc_id.id,
        #         'journal_id': writeoff_journal_id.id
        #     }
        #     if not all_aml_share_same_currency:
        #         writeoff_vals['amount_currency'] = False
        #     writeoff_to_reconcile = remaining_moves._create_writeoff(writeoff_vals)
        #     #add writeoff line to reconcile algo and finish the reconciliation
        #     remaining_moves = (remaining_moves + writeoff_to_reconcile).auto_reconcile_lines()
        #     return writeoff_to_reconcile
        return True
