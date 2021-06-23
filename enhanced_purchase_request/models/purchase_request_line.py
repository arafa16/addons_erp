from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SprogroupPurchaseRequestLineInherit(models.Model):
    _inherit = 'sprogroup.purchase.request.line'

    cost_product = fields.Float(string='Cost Price')
    subtotal = fields.Float(string='Sub Total', compute='set_price_total',)

    @api.onchange('product_id')
    def set_cost(self):
        if self.product_id.id == False:
            self.cost_product = 0
        else:
            self.cost_product = self.product_id.standard_price

    @api.depends('cost_product', 'product_qty')
    def set_price_total(self):
        for doc in self:
            doc.subtotal = doc.cost_product * doc.product_qty
    