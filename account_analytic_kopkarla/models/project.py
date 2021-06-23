from odoo import api, fields, models

class ProjectTask(models.Model):
    _inherit = "project.task"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete="cascade")
