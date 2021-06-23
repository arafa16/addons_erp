from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedMasterTtd(models.Model):
    _name = 'enhanced.master.ttd'

    name = fields.Char(string='Kategori')
    batas_atas = fields.Float(string='Batas Amount')