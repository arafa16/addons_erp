from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    kategorix = fields.Many2one('product.category',related='product_id.categ_id', string='Product Category',store=True)
    jumlahx = fields.Float(compute='_compute_total', string='Total', store=False)
    
    @api.multi
    @api.depends('price_unit')
    def _compute_total(self):
        for order_doc in self:
            order_doc.jumlahx = order_doc.product_uom_qty * order_doc.price_unit
    
    ww = 4