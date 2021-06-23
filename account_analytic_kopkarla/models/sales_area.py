from odoo import models, fields, api

class EnhancedSalesArea(models.Model):
    _inherit = 'enhanced.sales.area'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
