from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockLocationInherit(models.Model):
    _inherit = 'stock.location'

    gudang_ga = fields.Boolean(string='Gudang GA')
    