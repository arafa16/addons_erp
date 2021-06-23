from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedSalesApprovalInheritEmployee(models.Model):
    _inherit = 'hr.employee'

    sales_spv = fields.Boolean(string='SPV Sales')
    sales_assman = fields.Boolean(string='Assman Sales')
    otoritas_sales = fields.Many2many(comodel_name='tabel.ttd.sales', string='Sales Authority')