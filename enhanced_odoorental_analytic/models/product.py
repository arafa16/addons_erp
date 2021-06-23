from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedProductBecomeAnalytic(models.Model):
    _inherit = 'product.product'

    to_analytic = fields.Boolean(string='Rental Recurring')
    product_revese = fields.Many2one('product.product', string='Product Reverse', domain=[('to_analytic', '=', True)])