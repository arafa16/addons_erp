from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedStockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    produk_category = fields.Many2one('product.category', string='Produk Kategori', related="product_id.categ_id", store=True)