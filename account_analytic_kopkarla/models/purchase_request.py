from odoo import models, fields, api, _

class PurchaseRequest(models.Model):
    _inherit = 'sprogroup.purchase.request'

    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account') #, required=True)

    @api.onchange('analytic_account_id')
    def set_analytic_account(self):
        for line in self.line_ids:
            line.analytic_account_id = self.analytic_account_id.id

    @api.one
    @api.depends('requested_by')
    def _compute_department(self):
        super(PurchaseRequest, self)._compute_department()
        if (self.department_id.id == False):
            self.analytic_account_id = None
            return

        employee = self.env['hr.employee'].search([('work_email', '=', self.requested_by.email)])
        if (len(employee) > 0):
            self.analytic_account_id = employee[0].analytic_account_id.id
        else:
            self.analytic_account_id = None


class SprogroupPurchaseRequestLine(models.Model):
    _inherit = "sprogroup.purchase.request.line"

    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account')

    @api.onchange('product_qty')
    def set_analytic_account(self):
        if self.request_id.analytic_account_id:
            self.analytic_account_id = self.request_id.analytic_account_id.id