from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PeriodeRaport(models.Model):
    _name = 'res.partner.periode'

    name = fields.Char(string='Periode')
    tanggal1 = fields.Date(string='Tanggal Awal')
    tanggal2 = fields.Date(string='Tanggal Akhir')
