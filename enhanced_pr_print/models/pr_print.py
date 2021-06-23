from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PrPrint(models.Model):
    _inherit = 'sprogroup.purchase.request'
    ww = 4