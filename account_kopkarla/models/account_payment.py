from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class account_payment(models.Model):
    _inherit = "account.payment"

    payment_line_ids = fields.One2many('payment.journal.line', 'payment_invoice_id')

    created_sign_by = fields.Many2one('hr.employee', string='Dibuat', compute='_get_default_sign')
    checked_sign_by = fields.Many2one('hr.employee', string='Diperiksa', compute='_get_default_sign')
    known_sign_by = fields.Many2one('hr.employee', string='Mengetahui', compute='_get_default_sign')
    done_sign_by = fields.Many2one('hr.employee', string='Dilaksanakan', compute='_get_default_sign')
    management_sign_by = fields.Many2one('hr.employee', string='Pengurus', compute='_get_default_sign')

    def _get_default_sign(self):
        self.created_sign_by = self.env['res.config.settings'].get_values().get('default_created_sign_by')
        self.checked_sign_by = self.env['res.config.settings'].get_values().get('default_checked_sign_by')
        self.known_sign_by = self.env['res.config.settings'].get_values().get('default_known_sign_by')
        self.done_sign_by = self.env['res.config.settings'].get_values().get('default_done_sign_by')
        self.management_sign_by = self.env['res.config.settings'].get_values().get('default_management_sign_by')

    @api.multi
    def post_payment_journal(self, payment_journal):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                inv_open = ', '.join(['(%s - %s) %s' % (inv.id, inv.state, inv.number) for inv in rec.invoice_ids])
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!\n%s" % inv_open))

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
            move = rec._create_payment_journal_entry(payment_journal, amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
        return True

    def _create_payment_journal_entry(self, payment_journal, amount):
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            #if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)

        move = self.env['account.move'].create(self._get_move_vals())

        #Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        #Reconcile with the invoices
        payment_difference = payment_journal.payment_difference
        if self.payment_difference_handling == 'reconcile' and payment_difference:
        # if self.payment_difference_handling == 'reconcile' and self.payment_difference:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(payment_difference, self.currency_id, self.company_id.currency_id, invoice_currency)[2:]
            # the writeoff debit and credit must be computed from the invoice residual in company currency
            # minus the payment amount in company currency, and not from the payment difference in the payment currency
            # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
            total_residual_company_signed = sum(invoice.residual_company_signed for invoice in self.invoice_ids)
            residual_not_clear = sum(payment_journal.line_ids.search([('payment_id', '=', payment_journal.id), ('settle_full_invoice', '=', False)]).mapped('variance_amt'))
            if residual_not_clear > 0:
                total_residual_company_signed -= residual_not_clear
            total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(self.amount, self.company_id.currency_id)
            if payment_difference < 0:
                total_payment_company_signed += payment_difference
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
            if payment_difference > 0:
                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo

        #Write tax
        total_tax_amt = 0
        for line in payment_journal.line_ids:
            taxes = self.sudo().env['payment.journal.line.tax'].search([('payment_invoice_id', '=', line.id)])
            for tax in taxes:
            # for tax in line.sudo().tax_line_ids:
                aml_obj.create(self._prepare_tax_move_line_vals(aml_obj, move.id, line, tax, invoice_currency))
                total_tax_amt += tax.tax_amt

        #Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            if self.partner_type == 'customer':
                amount = self.amount - total_tax_amt + (payment_difference < 0 and payment_difference or 0)
                debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
                liquidity_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(amount))
            elif self.partner_type == 'supplier':
                amount = self.amount - total_tax_amt
                debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
                liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

        #validate the payment
        move.post()

        #reconcile the invoice receivable/payable line(s) with the payment
        # self.invoice_ids.register_payment(counterpart_aml)
        self.invoice_ids.register_payment_journal(counterpart_aml, payment_journal)

        return move

    def _prepare_tax_move_line_vals(self, aml_obj, move_id, line, tax, invoice_currency):
        amount = tax.tax_id.type_tax_use == 'sale' and tax.tax_amt or -tax.tax_amt
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
        vals = {
            'name': tax.tax_id.name,
            'account_id': tax.tax_id.account_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
            'date': self.payment_date,
            # 'debit': amount > 0 and amount,
            # 'credit': amount < 0 and abs(amount),
            'debit': debit,
            'credit': credit,
            # 'balance': amount,
            'partner_id': self.payment_type in ('inbound', 'outbound') and self.env['res.partner']._find_accounting_partner(self.partner_id).id or False,
            'invoice_id': line.invoice_id.id,
            'move_id': move_id,
            'amount_currency': amount_currency or False,
            'payment_id': self.id,
            'tax_line_id': tax.tax_id.id,
            'tax_no': tax.tax_no,
            'tax_date': tax.tax_date,
            # 'tax_base_amount': tax.base_amt,
        }
        return vals
