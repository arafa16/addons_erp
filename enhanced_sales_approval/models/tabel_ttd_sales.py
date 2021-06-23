from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TabelTtdPurchase(models.Model):
    _name = 'tabel.ttd.sales'
    _order = 'urutan asc'

    name = fields.Char(string='Kategori')
    next_step = fields.Many2one('tabel.ttd.sales', string='Parent Level')
    batas_atas = fields.Float(string='Batas Amount')
    urutan = fields.Integer(string='Sequence')
    batas_bawah = fields.Float(string='Batas Bawah')