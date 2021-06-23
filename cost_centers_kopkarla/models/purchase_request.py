from odoo import models, fields, api, _

class PurchaseRequest(models.Model):
    _inherit = 'sprogroup.purchase.request'

    cost_center_id = fields.Many2one("cost.center", string="Cost Center")

    @api.onchange('cost_center_id')
    def set_cost_center(self):
        for line in self.line_ids:
            line.cost_center_id = self.cost_center_id.id

    @api.one
    @api.depends('requested_by')
    def _compute_department(self):
        super(PurchaseRequest, self)._compute_department()
        if (self.department_id.id == False):
            self.cost_center_id = None
            return

        employee = self.env['hr.employee'].search([('work_email', '=', self.requested_by.email)])
        if (len(employee) > 0):
            self.cost_center_id = employee[0].cost_center_id.id
        else:
            self.cost_center_id = None


class SprogroupPurchaseRequestLine(models.Model):
    _inherit = "sprogroup.purchase.request.line"

    cost_center_id = fields.Many2one("cost.center", string="Cost Center")

    @api.onchange('product_qty')
    def set_cost_center(self):
        if self.request_id.cost_center_id:
            self.cost_center_id = self.request_id.cost_center_id.id
