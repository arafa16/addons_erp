from odoo import models, fields, api

class EnhancedSalesArea(models.Model):
    _inherit = "sale.order"

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                          readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                          help="The analytic account related to a sales order.", copy=True, oldname='project_id')

    @api.onchange('sales_area_kode')
    def set_analytic_account(self):
        self.analytic_account_id = self.sales_area_kode.analytic_account_id
