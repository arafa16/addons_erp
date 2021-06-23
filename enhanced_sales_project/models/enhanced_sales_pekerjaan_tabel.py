from odoo import models, fields, api

class EnhancedSalesProjectTabel(models.Model):
    _name = 'enhanced.sales.pekerjaan.tabel'
    _order = 'urutan asc'
    name = fields.Char(string='Jenis Pekerjaan')
    urutan = fields.Integer(string='Sequence')
    bypassLoA = fields.Boolean(string='ByPass LoA',default=False)
