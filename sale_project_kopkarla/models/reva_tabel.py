from odoo import models, fields, api


class RevaGroupTabel(models.Model):
    _name = 'enhanced.reva.group.tabel'
    _order = 'urutan asc'

    name = fields.Char(string='Reva')
    urutan = fields.Integer(string='Urutan')
    sale_reva_ids = fields.One2many('enhanced.reva.tabel', 'reva_id', string='Reva Status')


class RevaTabel(models.Model):
    _inherit = 'enhanced.reva.tabel'

    reva_id = fields.Many2one('enhanced.reva.group.tabel', string='Reva Group', ondelete='cascade')
