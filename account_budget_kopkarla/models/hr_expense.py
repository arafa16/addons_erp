from odoo import api, fields, models, _


class HrExpense(models.Model):
    _inherit = "hr.expense"
    
    accounting_date = fields.Date(string="Payment Date", related='sheet_id.accounting_date')
