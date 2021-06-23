from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectCost(models.Model):
    _name = 'epc.project.cost'

    name = fields.Char(string='Cost Description')
    quantity = fields.Integer(string='Quantity')
    cost = fields.Integer(string='Cost')
    uom = fields.Many2one('product.uom', string='Unit')
    sub_total = fields.Float(compute='get_price_total', string='Sub total', store=True)
    
    project_task = fields.Many2one('project.task', string='Project Task')

    @api.depends('quantity', 'cost')
    def get_price_total(self):
        for doc in self:
            doc.sub_total = doc.quantity * doc.cost
    