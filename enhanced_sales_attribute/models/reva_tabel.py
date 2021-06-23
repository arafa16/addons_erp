from odoo import models, fields, api

class RevaTabel(models.Model):
    _name = 'enhanced.reva.tabel'
    _order = 'jenis asc, urutan asc'
    name = fields.Char(string='Status')
    jenis = fields.Selection(selection=[('FPP', 'FPP'),('PR', 'PR')],default="FPP")
    urutan = fields.Integer(string='Urutan')