from odoo import models, fields, api

class MaterialRekuest(models.Model):
    _name = 'material.rekuest'

    name = fields.Char(string='Permintaan')
    approval = fields.Many2one('res.users', string='Approval')
    date_permintaan = fields.Date(string='Tanggal Permintaan', default=fields.Date.today())
    date_end = fields.Date(string='Tanggal Dibutuhkan')
    line_ids = fields.One2many(comodel_name='material.rekuest.line', inverse_name='mr_id', string='Product Line')
    description = fields.Text(string='Description')