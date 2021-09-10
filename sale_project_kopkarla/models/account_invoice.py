from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sale_id = fields.Many2one('sale.order', string='Sales Order')