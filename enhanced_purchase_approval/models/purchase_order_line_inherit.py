from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    kategorix = fields.Many2one('product.category', related='product_id.categ_id', string='Related Product Category', store=True,)
    qty_to_invoice = fields.Float(
        compute='_get_to_invoice_qty', string='To Invoice', store=True, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))
