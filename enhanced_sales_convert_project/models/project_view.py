from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectView(models.Model):
    _inherit = 'project.project'
    j_project = fields.Many2one('enhanced.sales.project.tabel', string='Jenis Project')
    j_pekerjaan = fields.Many2one('enhanced.sales.pekerjaan.tabel', string='Jenis Pekerjaan')
    nojar = fields.Char(string='Nomor Jaringan')
    # @api.model
    # def create(self, vals):
    #     cc = 4
    #     return super(ProjectView, self).create(vals)