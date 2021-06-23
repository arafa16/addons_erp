from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedProjectMrSalesOrder(models.Model):
    _inherit = 'sale.order'

    taskrel = fields.Many2one('project.task.type', string='Stage', related="task_id.stage_id",  store=True,)
    add_cost = fields.Float(string='Activity Cost', related="task_id.total_cost")