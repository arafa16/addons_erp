from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectTaskCost(models.Model):
    _inherit = 'project.task'

    project_costx = fields.One2many('epc.project.cost', 'project_task', string='Project Cost')
    total_cost = fields.Float(compute='_compute_total', string='Total Cost', store=True)
    data_teknis = fields.Text(string='Data Teknis')
    
    @api.multi
    @api.depends('project_costx')
    def _compute_total(self):
        for cost_doc in self:
            cost_total = sum(cost_doc.project_costx.mapped('sub_total'))
            cost_doc.total_cost = cost_total
    
    