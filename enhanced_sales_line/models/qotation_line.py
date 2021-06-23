from odoo import models, fields, api, _
from odoo.exceptions import UserError

class QotationLine(models.Model):
    _inherit = 'sale.order.line'
    tgl_delivery = fields.Date(string='Delivery date')
    
class QotationHeaderContent(models.Model):
    _inherit = 'sale.order'
    adaRental = fields.Boolean(string='')
    @api.multi
    def test_fn(self):
        qqq = 3
    