from odoo import api, fields, models

class ProjectTask(models.Model):
    _inherit = "project.task"

    cost_center_id = fields.Many2one("cost.center", string='Cost Center')

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.user_id.id)])
            if employee_id:
                self.cost_center_id = employee_id.cost_center_id.id
