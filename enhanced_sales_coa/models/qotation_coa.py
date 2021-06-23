from odoo import models, fields, api, _
from odoo.exceptions import UserError

class QotationCoa(models.Model):
    _inherit = 'sale.order'
    nomor_coa = fields.Many2one('account.account', string='Chart Of Account')