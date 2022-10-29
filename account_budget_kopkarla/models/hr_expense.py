from odoo import api, fields, models, _


class HrExpense(models.Model):
    _inherit = "hr.expense"
    
    accounting_date = fields.Date(string="Payment Date", related='sheet_id.accounting_date')
    # budget_lines_id = fields.Many2one('crossovered.budget.lines', 'Budget', compute='_get_budget_lines')
    #
    # def _get_budget_lines(self):
    #     for exp in self:
    #         exp.budget_lines_id = False