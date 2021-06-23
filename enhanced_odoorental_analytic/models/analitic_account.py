from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    sale_order_id = fields.Many2one('sale.order', string='Linking dengan Sale order')
