from odoo import models, fields, api, _
from odoo.exceptions import UserError

class QotationAttribute(models.Model):
    _inherit = 'sale.order'
    so_bagian = fields.Many2one('hr.department', string='Sales Dept')