from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit='purchase.order'

    cost_center_id = fields.Many2one("cost.center", string="Cost Center")

    # @api.onchange('cost_center_id')
    # def set_cost_center(self):
    #     for line in self.order_line:
    #         line.cost_center_id = self.cost_center_id.id

class PurchaseOrderLine(models.Model):
    _inherit='purchase.order.line'

    cost_center_id = fields.Many2one("cost.center", string="Cost Center",)

    # @api.onchange('product_qty')
    # def set_default_cost_center(self):
    #     if self.order_id.cost_center_id:
    #         self.cost_center_id = self.order_id.cost_center_id.id
