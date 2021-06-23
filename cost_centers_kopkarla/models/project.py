from odoo import api, fields, models

class ProjectTask(models.Model):
    _inherit = "project.task"

    cost_center_id = fields.Many2one("cost.center", string='Cost Center')
