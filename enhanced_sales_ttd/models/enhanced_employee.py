from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedEmployee(models.Model):
    
    _inherit = 'hr.employee'
    otoritas = fields.Many2many(comodel_name='enhanced.master.ttd', string='Otority')