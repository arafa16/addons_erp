from odoo import models, fields, api

class EnhancedSalesProjectTabel(models.Model):
    _inherit = 'enhanced.sales.project.tabel'

    project_account_id = fields.Many2one('account.account', 'Project Expense')
    project_income_id = fields.Many2one('account.account', 'Project Income')
    # jenis_so = fields.Selection([("Project", "Project"), ("datacom", "Trading Datacom")], string='Order Type')
