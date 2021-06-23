from odoo import models, fields, api, _

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    cost_center_id = fields.Many2one("cost.center", string="Cost Center")

    @api.onchange('cost_center_id')
    def set_cost_center(self):
        for line in self.line_ids:
            line.cost_center_id = self.cost_center_id.id

    # @api.onchange('account_analytic_id')
    # def set_analytic_account(self):
    #     for line in self.line_ids:
    #         line.account_analytic_id = self.account_analytic_id.id

class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    cost_center_id = fields.Many2one("cost.center", string="Cost Center")

    @api.onchange('product_qty')
    def set_cost_center(self):
        if self.requisition_id.cost_center_id:
            self.cost_center_id = self.requisition_id.cost_center_id.id

    # @api.onchange('product_qty')
    # def set_analytic_account(self):
    #     if self.requisition_id.ccount_analytic_aid:
    #         self.account_analytic_id = self.requisition_id.account_analytic_id.id

    @api.multi
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        res = super(PurchaseRequisitionLine, self)._prepare_purchase_order_line(name, product_qty, price_unit, taxes_ids)
        res['cost_center_id'] = self.cost_center_id.id
        res['account_analytic_id'] = self.account_analytic_id.id
        return res
