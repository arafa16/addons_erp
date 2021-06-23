from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pegawai_ttd = fields.Many2one('hr.employee', string='Otoritas Tandatangan')