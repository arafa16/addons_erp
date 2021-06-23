from odoo import api, models, fields

class HREmployee(models.Model):

    _inherit='hr.employee'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete="cascade")

    @api.onchange('department_id')
    def _onchange_analytic_account_id(self):
        if self.department_id:
            department = self.env['hr.department'].search([('id', '=', self.department_id[0].id)])
            self.analytic_account_id = department[0].analytic_account_id.id
        else:
            self.analytic_account_id = None

class Department(models.Model):
    _inherit = "hr.department"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete="cascade")
