from odoo import models, fields, api

class EnhancedSalesProjectTabel(models.Model):
    _name = 'enhanced.sales.jenis.tabel'
    _order = 'urutan asc'
    name = fields.Char(string='Jenis Order')
    bypassLoA = fields.Boolean(string='ByPass LoA',default=False)
    urutan = fields.Integer(string='Sequence')