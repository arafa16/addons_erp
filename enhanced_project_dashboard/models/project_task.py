from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectTaskVendor(models.Model):
    _inherit = 'project.task'

    pelaksana_kerja = fields.Selection([("internal","Internal"),("vendor","Vendor Pihak Ketiga")], string='Pelaksana', default='internal')
    pihak_ke_tiga = fields.Many2one('res.partner', string='Vendor Pelaksana')