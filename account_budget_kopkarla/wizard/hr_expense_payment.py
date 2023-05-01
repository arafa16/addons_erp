# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from werkzeug import url_encode

class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
    _inherit = "hr.expense.payment.wizard"

    def update_budget(self):
        expenses = self.env['hr.expense'].read_group(
            domain=[('budget_lines_id', '!=', False), ('sheet_id', '=', self.sheet_id.id)],
            fields=['budget_lines_id', 'total_amount'],
            groupby=['budget_lines_id']
        )
        for exp in expenses:
            expense = self.env['hr.expense'].search([('sheet_id', '=', self.sheet_id.id), ('budget_lines_id', '=', exp.get('budget_lines_id')[0])], limit=1)
            line_id = {
                'budget_account_id': expense.account_id.id,
                'cost_center_id': self.sheet_id.cost_center_id.id,
                'analytic_account_id': self.sheet_id.analytic_account_id.id,
                'selected_budget_id': expense.budget_lines_id.id,
                'restrict_allow': expense.budget_lines_id.restrict_allow,
                'requested_amount': exp.get('total_amount'),
            }
            budget_request_id = self.env['budget.request'].create({
                'name': 'Budget Expense %s' % self.sheet_id.name,
                'date': self.sheet_id.report_date,
                'origin': 'expense_request',
                'sheet_id': self.sheet_id.id,
                'state': 'done',
                'line_ids': [[0, 0, line_id]],
            })
            if budget_request_id.line_ids[0].outstanding_running_budget < 0 and expense.budget_lines_id.restrict_allow == 'restrict':
                raise UserError(_("Budget %s kurang Rp %s." % (expense.budget_lines_id.display_name, '{:,.2f}'.format(abs(budget_request_id.line_ids[0].outstanding_running_budget)))))

            self.env['hr.expense'].search([('sheet_id', '=', self.sheet_id.id), ('budget_lines_id', '=', exp.get('budget_lines_id')[0])]).update({'budget_request_line_id': budget_request_id.line_ids[0].id})

    @api.multi
    def expense_post_payment(self):
        self.update_budget()
        return super(HrExpenseSheetRegisterPaymentWizard, self).expense_post_payment()