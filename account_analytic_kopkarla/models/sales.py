from odoo import models, fields, api

class EnhancedSalesArea(models.Model):
    _inherit = "sale.order"

    @api.onchange('sales_area_kode')
    def set_analytic_account(self):
        self.analytic_account_id = self.sales_area_kode.analytic_account_id
