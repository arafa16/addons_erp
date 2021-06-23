from odoo import api, models, fields

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoices_cancel(self):
        for invoice in self:
            invoice.action_invoice_cancel()