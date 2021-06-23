from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    FakturNumber = fields.Char(string='E-Faktur Number')
    FakturDate = fields.Date(string='E-Faktur Date')