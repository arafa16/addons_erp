from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MasterAlokasiPerangkat(models.Model):
    _name = 'alokasi.perangkat'
    _order = 'sequence asc'
    name = fields.Char(string='Perangkat')
    sequence = fields.Integer(string='Sequence')