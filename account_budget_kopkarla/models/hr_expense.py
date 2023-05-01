from odoo import api, fields, models, _


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    active_budget_count = fields.Integer(string='Active Budget', compute='_compute_active_budget_count',)

    def _compute_active_budget_count(self):
        budget_model = self.env['crossovered.budget.lines']
        # today = fields.Date.today()
        domain = [
                ('date_from', '<=', self.report_date),
                ('date_to', '>=', self.report_date),
                ('cost_center_id', '=', self.cost_center_id.id),
                ('analytic_account_id', '=', self.analytic_account_id.id),
                ('id', 'in', self.expense_line_ids.filtered(lambda b: b.budget_lines_id).mapped('budget_lines_id').ids),
                ('state', '=', 'ready'),
            ]
        fetch_data = budget_model.read_group(domain, [], [], lazy=False)
        result = [data['__count'] for data in fetch_data]
        self.active_budget_count = str(result[0])

    def show_available_budget(self):
        view = self.env.ref('account_budget_kopkarla.view_account_budget_available_tree_expense')
        form = self.env.ref('account_budget_kopkarla.view_account_budget_available_form')
        search_view = self.env.ref('account_budget_kopkarla.view_account_budget_available_search')

        # context = {'group_by': 'general_budget_id'}
        context = {}
        # context = {'budget_adjustment_id': self.id,
        #             'budget_position': self.env.context.get('budget_position'),
        #         }
        domain = [('date_from', '<=', self.report_date), ('date_to', '>=', self.report_date), ('state', '=', 'ready'),
                  ('id', 'in', self.expense_line_ids.filtered(lambda b: b.budget_lines_id).mapped('budget_lines_id').ids),
                  ]
        if self.cost_center_id:
            domain.append(('cost_center_id', '=', self.cost_center_id.id))
        if self.analytic_account_id:
            domain.append(('analytic_account_id', '=', self.analytic_account_id.id))

            # context.update({'cost_center_adj': self.cost_center_id_adj.id})
            # context.update({'analytic_account_adj': self.analytic_account_id_adj.id})
        return {
            'name': 'Available Budgets',
            'type': 'ir.actions.act_window',
            # 'view_type': 'form',
            # 'view_mode': 'tree,form',
            'res_model': 'crossovered.budget.lines',
            'views': [(view.id, 'tree'), (form.id, 'form')],
            # 'view_id': view.id,
            'target': 'current',
            'search_view_id': search_view.id,
            # 'limit': 5,
            'domain': domain,
            'context': context,
        }

    @api.multi
    def cancel(self):
        for budget_request_line_id in self.expense_line_ids.filtered(lambda b: b.budget_request_line_id).mapped('budget_request_line_id'):
            budget_request_line_id.budget_request_id.unlink()
        super(HrExpenseSheet, self).cancel()


class HrExpense(models.Model):
    _inherit = "hr.expense"
    
    accounting_date = fields.Date(string="Payment Date", related='sheet_id.accounting_date')
    budget_lines_id = fields.Many2one('crossovered.budget.lines', 'Budget', compute='_get_budget_lines', store=True)
    budget_request_line_id = fields.Many2one('budget.request.line', string='Budget Request', readonly=True, ondelete='set null')

    @api.onchange('product_id')
    def _get_budget_lines(self):
        for exp in self:
            exp.budget_lines_id = False
            budget_postition_id = self.env['account.budget.post'].sudo().search([('account_ids', '=', exp.product_id.property_account_expense_id.id)], limit=1)
            if budget_postition_id:
                budget_line_id = self.env['crossovered.budget.lines'].sudo().search([
                    ('general_budget_id', '=', budget_postition_id.id),
                    ('cost_center_id', '=', exp.sheet_id.cost_center_id.id),
                    ('analytic_account_id', '=', exp.sheet_id.analytic_account_id.id),
                    ('date_from', '<=', exp.sheet_id.report_date), #exp.accounting_date or exp.date),
                    ('date_to', '>=', exp.sheet_id.report_date), #exp.accounting_date or exp.date),
                    ('state', '=', 'ready'),
                ])
                if budget_line_id:
                    exp.budget_lines_id = budget_line_id.id