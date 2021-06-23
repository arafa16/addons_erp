from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ESProjectTaskType(models.Model):
    _inherit = 'project.task.type'
    jenis_pek = fields.Many2many(comodel_name='enhanced.sales.pekerjaan.tabel', string='Jenis Pekerjaan')
    
    ww = 4