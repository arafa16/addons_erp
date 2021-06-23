from odoo import models, fields

class Department(models.Model):
    _inherit = "hr.department"

    cost_center_id = fields.Many2one('cost.center', string="Cost Center")