from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
# from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
# from odoo.http import request


class BudgetRequest(models.Model):
    _name = "budget.realization"
    _description = "Budget Realization Table"
    # _order = "date desc, id desc"

    # READONLY_STATES = {
    #     'draft': [('readonly', False)],
    #     'done': [('readonly', True)],
    #     'cancel': [('readonly', True)],
    # }

    name = fields.Char(string='Name', index=True, required=True, help='The name that will be used on budget request control')
    date = fields.Datetime('Date', required=True, index=True, copy=False, default=fields.Datetime.now)
    description = fields.Text('Description')
    origin = fields.Selection([('purchase_request', 'Purchase Request'),], readonly=True, required=True, default='purchase_request')
    origin_ref = fields.Char("Reference")
    line_ids = fields.One2many('budget.realization.line', 'budget_realization_id', string='Budget Lines', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft')

    @api.multi
    def budget_realization_approve_action(self):
        msg = ''
        is_approved = True
        if self.env.context.get('force') == 0:
            for real in self.line_ids:
                if real.restrict_allow != 'allow':
                    if real.requested_amount > real.available_budget:
                        msg = (real.selected_budget_id and '%sRequested amount on %s is larger than available budget.\n' % (msg, real.budget_account_id.name)) or \
                              '%sAccount %s has no budget selected.\n' % (msg, real.budget_account_id.name)
                        if real.restrict_allow == 'restrict' or not real.selected_budget_id:
                            is_approved = False

        if is_approved:
            self.date = datetime.now()
            self.state = 'done'
            self.request_id.request_budget_approval()
            if msg:
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                return {
                    'name': 'Warning: Budget approved',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': {'message': msg},
                }
        else:
            msg = '%s\nBudget requested is not approved yet.' % msg
            raise UserError(msg)

    @api.onchange('date')
    def _onchange_date(self):
        for line in self.line_ids:
            line.selected_budget_id = False
            line.available_budget = False
            line.restrict_allow = False

            criteria = [('date_from', '<=', self.date), ('date_to', '>=', self.date)]
            general_budget_ids = self.env['account.budget.post'].search(
                [('account_ids', '=', line.budget_account_id.id)])
            budget_ids = []
            for general_budget_id in general_budget_ids:
                budget_ids.append(general_budget_id.id)
            if budget_ids:
                criteria.append(('general_budget_id', 'in', budget_ids))
            if line['cost_center_id']:
                criteria.append(('cost_center_id', '=', line.cost_center_id.id))
            if line['analytic_account_id']:
                criteria.append(('analytic_account_id', '=', line.analytic_account_id.id))

            # appropriate_budget = self.env['crossovered.budget.lines'].sudo().search(criteria, limit=1)
            appropriate_budgets = self.env['crossovered.budget.lines'].search(criteria)
            for appropriate_budget in appropriate_budgets:
                if appropriate_budget.crossovered_budget_id.state == 'validate':
                    # line['sequence'] = i
                    line.selected_budget_id = appropriate_budget.id
                    line.available_budget = -appropriate_budget.avail_req_amount
                    line.restrict_allow = appropriate_budget.restrict_allow
                    break


class BudgetRequestLine(models.Model):
    _name = "budget.realization.line"
    _description = "Budget Realization Lines"
    _rec_name = "selected_budget_id"

    budget_request_id = fields.Many2one('budget.request', string='Budget Realization', index=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=1)
    purchase_request_line_ids = fields.One2many('sprogroup.purchase.request.line', 'budget_realization_line_id', 'Realization Lines', readonly=True)
    # name = fields.Text(string='Description')
    budget_account_id = fields.Many2one('account.account', 'Budget Account', readonly=True)
    cost_center_id = fields.Many2one("cost.center", string='Cost Center', ondelete="cascade", readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete="cascade", readonly=True)
    realization_amount = fields.Float(string='Realization Amount', readonly=True)
    selected_budget_id = fields.Many2one('crossovered.budget.lines', string='Selected Budget', ondelete="cascade", readonly=True)
    available_budget = fields.Float(string='Available Budget', readonly=True)
    restrict_allow = fields.Selection([('allow','Allow'),('restrict' , 'Restricted'),('warn','Warning')],string="Budget Control", readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', compute='_get_budget_state', method=True)

    @api.one
    def _get_budget_state(self):
        self.state = self.budget_request_id.state

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         record_name = record.crossovered_budget_id.name + ' - ' + record.general_budget_id.name
    #         result.append((record.id, record_name))
    #     return result

    # @api.model
    # def budget_requested_amount(self, budget_line_id):
    #     requested_recs = self.search([('selected_budget_id', '=', budget_line_id)])
    #     result = 0
    #     for rec in requested_recs:
    #         result += rec.requested_amount
    #     return result

    #
    # @api.multi
    # def show_available_budget(self):
    #     a = 1

# class BudgetRequestLinePosition(models.Model):
#     _name = "budget.request.line.position"
#     _rec_name = "budget_position_id"
#     _description = "Budget Request Line Position"
#
#     budget_request_line_id = fields.Many2one('budget.request.line', string='Budget Request Line', index=True, required=True, ondelete='cascade')
#     budget_line_id = fields.Many2one('crossovered.budget.lines', string='Budget Available', ondelete="cascade")
