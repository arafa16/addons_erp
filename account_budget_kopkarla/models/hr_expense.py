from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    active_budget_count = fields.Integer(string='Active Budget', compute='_compute_active_budget_count',)
    state = fields.Selection(selection_add_after={'submit': [('budget', 'Budget')]})
    budget_request_id = fields.Many2one('budget.request', 'Budget Request', compute='_get_budget_request')

    def _get_budget_request(self):
        for sheet in self:
            sheet.budget_request_id = self.env['budget.request'].sudo().search([('sheet_id', '=', sheet.id)]).id

    @api.onchange('cost_center_id','analytic_account_id','report_date')
    def _onchange_budget(self):
        for exp in self.expense_line_ids:
            exp.budget_lines_id = exp._get_budget_line(exp.product_id.property_account_expense_id.id, self.cost_center_id.id, self.analytic_account_id.id, self.report_date)

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

    def show_selected_budget(self):
        budget_approval_view_id = self.env.ref('account_budget_kopkarla.view_budget_request_form')
        return {
            'name': _('Budget Approval'),
            'res_model': 'budget.request',
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'view_mode': 'form',
            'view_id': budget_approval_view_id.id,
            'target': 'current',
            'res_id': self.budget_request_id.id,
        }

        # view = self.env.ref('account_budget_kopkarla.view_account_budget_available_tree_expense')
        # form_view = self.env.ref()
        # search_view = self.env.ref('account_budget_kopkarla.view_account_budget_available_search')

        # context = {'group_by': 'general_budget_id'}
        # context = {}
        # # context = {'budget_adjustment_id': self.id,
        # #             'budget_position': self.env.context.get('budget_position'),
        # #         }
        # domain = [('date_from', '<=', self.report_date), ('date_to', '>=', self.report_date), ('state', '=', 'ready'),
        #           ('id', 'in',
        #            self.expense_line_ids.filtered(lambda b: b.budget_lines_id).mapped('budget_lines_id').ids),
        #           ]
        # if self.cost_center_id:
        #     domain.append(('cost_center_id', '=', self.cost_center_id.id))
        # if self.analytic_account_id:
        #     domain.append(('analytic_account_id', '=', self.analytic_account_id.id))

            # context.update({'cost_center_adj': self.cost_center_id_adj.id})
            # context.update({'analytic_account_adj': self.analytic_account_id_adj.id})
        # return {
        #     'name': 'Available Budgets',
        #     'type': 'ir.actions.act_window',
        #     # 'view_type': 'form',
        #     # 'view_mode': 'tree,form',
        #     'res_model': 'budget.request',
        #     'views': [(form_view.id, 'form')],
        #     # 'view_id': view.id,
        #     'target': 'current',
        #     # 'search_view_id': search_view.id,
        #     # 'limit': 5,
        #     'domain': domain,
        #     'context': context,
        # }

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

    def update_budget(self, state):
        expenses = self.env['hr.expense'].read_group(
            domain=[('budget_lines_id', '!=', False), ('sheet_id', '=', self.id)],
            fields=['budget_lines_id', 'total_amount'],
            groupby=['budget_lines_id']
        )
        for exp in expenses:
            expense = self.env['hr.expense'].search([('sheet_id', '=', self.id), ('budget_lines_id', '=', exp.get('budget_lines_id')[0])], limit=1)
            line_id = {
                'budget_account_id': expense.account_id.id,
                'cost_center_id': self.cost_center_id.id,
                'analytic_account_id': self.analytic_account_id.id,
                'selected_budget_id': expense.budget_lines_id.id,
                'restrict_allow': expense.budget_lines_id.restrict_allow,
                'requested_amount': exp.get('total_amount'),
            }
            budget_request_id = self.env['budget.request'].create({
                'name': 'Budget Expense %s' % self.name,
                'date': self.report_date,
                'origin': 'expense_request',
                'sheet_id': self.id,
                'state': state,
                'line_ids': [[0, 0, line_id]],
            })
            if state == 'done' and budget_request_id.line_ids[0].outstanding_running_budget < 0 and expense.budget_lines_id.restrict_allow == 'restrict':
                raise UserError(_("Budget %s kurang Rp %s." % (expense.budget_lines_id.display_name, '{:,.2f}'.format(abs(budget_request_id.line_ids[0].outstanding_running_budget)))))

            self.env['hr.expense'].search([('sheet_id', '=', self.id), ('budget_lines_id', '=', exp.get('budget_lines_id')[0])]).update({'budget_request_line_id': budget_request_id.line_ids[0].id})

    @api.multi
    def budget_approval(self):
        for sheet in self:
            for exp in sheet.expense_line_ids:
                if not exp.budget_lines_id:
                    exp.budget_lines_id = exp._get_budget_line(exp.account_id.id, sheet.cost_center_id.id, sheet.analytic_account_id.id, sheet.report_date)
                if not exp.budget_lines_id:
                    raise UserError(_("Budget is empty!"))
            sheet.state = 'budget'
            sheet.update_budget('draft')

    @api.model
    def create(self, vals):
        sheet = super(HrExpenseSheet, self).create(vals)
        for exp in sheet.expense_line_ids:
            if not exp.budget_lines_id:
                exp.budget_lines_id = exp._get_budget_line(exp.account_id.id, self.cost_center_id.id, self.analytic_account_id.id, self.report_date)
            # if not exp.budget_lines_id:
            #     raise UserError(_("Budget is empty!"))
        return sheet

    @api.multi
    def write(self, vals):
        res = super(HrExpenseSheet, self).write(vals)
        for exp in self.expense_line_ids:
            if not exp.budget_lines_id:
                exp.budget_lines_id = exp._get_budget_line(exp.account_id.id, self.cost_center_id.id, self.analytic_account_id.id, self.report_date)
            # if not exp.budget_lines_id:
            #     raise UserError(_("Budget is empty!"))
        return res

    @api.multi
    def cancel(self):
        for budget_request_line_id in self.expense_line_ids.filtered(lambda b: b.budget_request_line_id).mapped('budget_request_line_id'):
            budget_request_line_id.budget_request_id.unlink()
        super(HrExpenseSheet, self).cancel()

    @api.multi
    def refuse_sheet(self, reason):
        budget_id = self.env['budget.request'].sudo().search([('sheet_id', '=', self.id)])
        if budget_id:
            budget_id.unlink()
        super(HrExpenseSheet, self).refuse_sheet(reason)

    @api.multi
    def approve_expense_sheets(self):
        for sheet in self:
            if not sheet.is_unbudget:
                for exp in sheet.expense_line_ids:
                    if not exp.budget_lines_id:
                        exp.budget_lines_id = exp._get_budget_line(exp.account_id.id, sheet.cost_center_id.id, sheet.analytic_account_id.id, sheet.report_date)
                    if not exp.budget_lines_id:
                        raise UserError(_("Budget is empty!"))
        self.update_budget('done')
        super(HrExpenseSheet, self).approve_expense_sheets()


class HrExpense(models.Model):
    _inherit = "hr.expense"
    
    accounting_date = fields.Date(string="Payment Date", related='sheet_id.accounting_date')
    budget_lines_id = fields.Many2one('crossovered.budget.lines', 'Budget', compute='_get_budget_lines', store=True)
    budget_request_line_id = fields.Many2one('budget.request.line', string='Budget Request', readonly=True, ondelete='set null')

    def _get_budget_line(self, account_id, cost_center_id, analytic_account_id, date):
        budget_postition_id = self.env['account.budget.post'].sudo().search([('account_ids', '=', account_id)], limit=1)
        if budget_postition_id:
            budget_line_id = self.env['crossovered.budget.lines'].sudo().search([
                ('general_budget_id', '=', budget_postition_id.id),
                ('cost_center_id', '=', cost_center_id),
                ('analytic_account_id', '=', analytic_account_id),
                ('date_from', '<=', date),  # exp.accounting_date or exp.date),
                ('date_to', '>=', date),  # exp.accounting_date or exp.date),
                ('state', '=', 'ready'),
            ])
            return budget_line_id.id if budget_line_id else False
        return False

    @api.onchange('product_id')
    def _get_budget_lines(self):
        for exp in self:
            account_id = exp.account_id | exp.product_id.property_account_expense_id
            exp.budget_lines_id = self._get_budget_line(account_id.id, exp.sheet_id.cost_center_id.id, exp.sheet_id.analytic_account_id.id, exp.sheet_id.report_date)
            # exp.budget_lines_id = False
            # budget_postition_id = self.env['account.budget.post'].sudo().search([('account_ids', '=', exp.product_id.property_account_expense_id.id)], limit=1)
            # if budget_postition_id:
            #     budget_line_id = self.env['crossovered.budget.lines'].sudo().search([
            #         ('general_budget_id', '=', budget_postition_id.id),
            #         ('cost_center_id', '=', exp.sheet_id.cost_center_id.id),
            #         ('analytic_account_id', '=', exp.sheet_id.analytic_account_id.id),
            #         ('date_from', '<=', exp.sheet_id.report_date), #exp.accounting_date or exp.date),
            #         ('date_to', '>=', exp.sheet_id.report_date), #exp.accounting_date or exp.date),
            #         ('state', '=', 'ready'),
            #     ])
            #     if budget_line_id:
            #         exp.budget_lines_id = budget_line_id.id

    @api.onchange('account_id')
    def _get_account_budget_lines(self):
        for exp in self:
            exp.budget_lines_id = self._get_budget_line(exp.account_id.id, exp.sheet_id.cost_center_id.id, exp.sheet_id.analytic_account_id.id, exp.sheet_id.report_date)
            # exp.budget_lines_id = False
            # budget_postition_id = self.env['account.budget.post'].sudo().search([('account_ids', '=', exp.account_id.id)], limit=1)
            # if budget_postition_id:
            #     budget_line_id = self.env['crossovered.budget.lines'].sudo().search([
            #         ('general_budget_id', '=', budget_postition_id.id),
            #         ('cost_center_id', '=', exp.sheet_id.cost_center_id.id),
            #         ('analytic_account_id', '=', exp.sheet_id.analytic_account_id.id),
            #         ('date_from', '<=', exp.sheet_id.report_date), #exp.accounting_date or exp.date),
            #         ('date_to', '>=', exp.sheet_id.report_date), #exp.accounting_date or exp.date),
            #         ('state', '=', 'ready'),
            #     ])
            #     if budget_line_id:
            #         exp.budget_lines_id = budget_line_id.id
