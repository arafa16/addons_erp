from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedInventoryProduct(models.Model):
    _inherit = 'product.product'

    ww = 4

    