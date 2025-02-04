from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class account_payment(models.Model):
    _inherit = "account.payment"

    sheet_ids = fields.One2many('hr.expense.sheet', 'payment_id', 'Expense')
    advance_ids = fields.One2many('hr.advance', 'payment_id', 'Advance')

    @api.multi
    def post_expense(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state not in ('post', 'done') for inv in rec.sheet_ids):
                raise ValidationError(_("The payment cannot be processed because the expense is not posted!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_expense_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'reconciled', 'move_name': move.name})
        return True

    def _get_counterpart_expense_move_line_vals(self, sheet_ids):
        name = "Expense Payment"
        if sheet_ids:
            name += ': '
            for exp in sheet_ids:
                if exp.move_id:
                    name += exp.name + ', '
            name = name[:len(name)-2]
        return {
            'name': name,
            'account_id': self.destination_account_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
        }

    def _create_payment_expense_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references expense(s) they are reconciled.
            Return the journal entry.
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        expense_currency = False
        if self.sheet_ids and all([x.currency_id == self.sheet_ids[0].currency_id for x in self.sheet_ids]):
            #if all the expenses selected share the same currency, record the paiement in that currency too
            expense_currency = self.sheet_ids[0].currency_id
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, expense_currency)

        move = self.env['account.move'].create(self._get_move_vals())
        self.sheet_ids[0].update({'move_id': move.id})
        #Write line corresponding to expense payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_expense_move_line_vals(self.sheet_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        #Reconcile with the expenses
        if self.payment_difference_handling == 'reconcile' and self.payment_difference:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id, expense_currency)[2:]
            # the writeoff debit and credit must be computed from the expense residual in company currency
            # minus the payment amount in company currency, and not from the payment difference in the payment currency
            # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
            total_residual_company_signed = sum(invoice.residual_company_signed for invoice in self.invoice_ids)
            total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(self.amount, self.company_id.currency_id)
            # amout_wo must be positive for out_invoice and in_refund and negative for in_invoice and out_refund in standard use case
            #               |   total_payment_company_signed   |    total_residual_company_signed    |    amount_wo
            #----------------------------------------------------------------------------------------------------------------------
            # in_invoice    |   positive                       |    positive                         |    negative
            #----------------------------------------------------------------------------------------------------------------------
            # in_refund     |   positive                       |    negative                         |    positive
            #----------------------------------------------------------------------------------------------------------------------
            # out_invoice   |   positive                       |    positive                         |    positive
            #----------------------------------------------------------------------------------------------------------------------
            # out_refund    |   positive                       |    negative                         |    negative
            #----------------------------------------------------------------------------------------------------------------------
            # DO NOT FORWARD-PORT
            if self.invoice_ids[0].type == 'in_invoice':
                amount_wo = total_payment_company_signed - total_residual_company_signed
            elif self.invoice_ids[0].type == 'in_refund':
                amount_wo = - total_payment_company_signed - total_residual_company_signed
            elif self.invoice_ids[0].type == 'out_refund':
                amount_wo = total_payment_company_signed + total_residual_company_signed
            else:
                amount_wo = total_residual_company_signed - total_payment_company_signed
            # Align the sign of the secondary currency writeoff amount with the sign of the writeoff
            # amount in the company currency
            if amount_wo > 0:
                debit_wo = amount_wo
                credit_wo = 0.0
                amount_currency_wo = abs(amount_currency_wo)
            else:
                debit_wo = 0.0
                credit_wo = -amount_wo
                amount_currency_wo = -abs(amount_currency_wo)
            writeoff_line['name'] = self.writeoff_label
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo

        #Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            # ----> remark karena coa payment keliru
            if self.sheet_ids and all([x.currency_id == self.sheet_ids[0].currency_id for x in self.sheet_ids]) and self.sheet_ids[0].total_amount < 0:
                liquidity_aml_dict['account_id'] = self.sheet_ids[0].partner_id.property_account_receivable_id.id
            aml_obj.create(liquidity_aml_dict)

        #validate the payment
        move.post()

        if self.partner_type:
            #reconcile the expense line(s) with the payment
            self.sheet_ids.register_payment(counterpart_aml)

        return move

    def _get_counterpart_move_line_vals(self, invoice=False):
        if self.partner_id and not (self.partner_id.customer or self.partner_id.supplier):
            return {
                'name': self.communication, # self.name,
                'account_id': self.destination_account_id.id,
                'journal_id': self.journal_id.id,
                'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
                'payment_id': self.id,
            }
        else:
            return super(account_payment, self)._get_counterpart_move_line_vals(invoice)
