from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    kategorix = fields.Many2one('product.category', related='product_id.categ_id', string='Related Product Category', store=True,)