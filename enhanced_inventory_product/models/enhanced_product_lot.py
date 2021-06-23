from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedProductLot(models.Model):
    _inherit = 'stock.production.lot'

    keterangan = fields.Char(string='Keterangan')
    