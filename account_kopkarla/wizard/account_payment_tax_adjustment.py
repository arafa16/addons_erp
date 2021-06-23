# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class PaymentTaxAdjustmentJournal(models.TransientModel):
    _name = "payment.journal.tax.adjustment"
    _rec_name = 'payment_id'
    _description = "Payment Journal Tax Adjustment"

    payment_id = fields.Many2one('payment.journal', string="Payment", required=True, readonly=True, ondelete='cascade', index=True)
    payment_tax_id = fields.Many2one('payment.journal.line.tax', string="Select PPH")
    date = fields.Date(string='Tax Adjust Date', default=fields.Date.context_today)
    description = fields.Char(string='Reason', required=True)
    filter_adj = fields.Selection([('cancel', 'Remove PPH, create vendor bill')], default='cancel', string='Adjustment Method', required=True)

    def adjust_pph(self):
        val = {
            'name': dict(self._fields['filter_adj'].selection).get(self.filter_adj),
            'date': self.date,
            'description':self.description,
            'payment_id': self.payment_id.id,
            'payment_invoice_id': self.payment_tax_id.payment_invoice_id.id,
            'tax_id': self.payment_tax_id.tax_id.id,
            'currency_id': self.payment_tax_id.currency_id.id,
            'base_amt': self.payment_tax_id.base_amt,
            'tax_pct': self.payment_tax_id.tax_pct,
            'tax_amt': self.payment_tax_id.tax_amt,
            'tax_no': self.payment_tax_id.tax_no,
            'tax_date': self.payment_tax_id.tax_date,
            'state': 'draft'
        }
        tax_adjust = self.env['payment.journal.line.tax.adjust'].create(val)
        tax_adjust.post()