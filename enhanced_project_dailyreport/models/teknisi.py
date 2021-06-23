from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DailyTeknisi(models.Model):
    _name = 'daily.teknisi'

    _order = 'sequence asc'
    name = fields.Char(string='TEKNISI')
    sequence = fields.Integer(string='Sequence')