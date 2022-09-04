# -*- coding: utf-8 -*-
# (C) 2014 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from lxml import etree
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.osv.orm import setup_modifiers
from odoo import tools

# from lxml import etree

class Budget(models.Model):
    _inherit = 'crossovered.budget'

    cost_center_id = fields.Many2one("cost.center", string='Cost Center', required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', required=True)

    @api.onchange('cost_center_id')
    def _onchange_cost_center_id(self):
        for budget in self:
            for line in budget.crossovered_budget_line:
                line.cost_center_id = self.cost_center_id.id

    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_id(self):
        for budget in self:
            for line in budget.crossovered_budget_line:
                line.analytic_account_id = self.analytic_account_id.id

    @api.onchange('date_from', 'date_to')
    def update_budget_line_period(self):
        for line in self.crossovered_budget_line:
            line.update({'date_from': self.date_from,
                         'date_to': self.date_to})

    def change_state_budget_line(self):
        for budget_line in self.crossovered_budget_line:
            budget_line.state = (self.state == 'validate' and 'ready') or \
                                (self.state == 'done' and 'close') or \
                                'draft'

    @api.multi
    def unlink(self):
        for budget in self:
            if budget.state not in ['draft', 'cancel']:
                raise UserError(_('You cannot delete a document that not in draft / cancel state.'))
        super(Budget, self).unlink()

    @api.multi
    def action_budget_confirm(self):
        for budget in self:
            for line in budget.crossovered_budget_line:
                line._validate_sign_planned_amount()
            budget.write({'state': 'confirm'})
            budget.change_state_budget_line()

    @api.multi
    def action_budget_draft(self):
        for budget in self:
            budget.write({'state': 'draft'})
            budget.change_state_budget_line()

    @api.multi
    def action_budget_validate(self):
        for budget in self:
            budget.write({'state': 'validate'})
            budget.change_state_budget_line()

    @api.multi
    def action_budget_cancel(self):
        for budget in self:
            budget.write({'state': 'cancel'})
            budget.change_state_budget_line()

    @api.multi
    def action_budget_done(self):
        for budget in self:
            budget.write({'state': 'done'})
            budget.change_state_budget_line()


class BudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'

    general_budget_id = fields.Many2one('account.budget.post', required=True)
    cost_center_id = fields.Many2one("cost.center", string='Cost Center') #, required=True)
    analytic_line_ids = fields.One2many('account.analytic.line', 'budget_line_id', 'Analytic Lines', copy=False)
    restrict_allow = fields.Selection([('allow','Allow'),('restrict' , 'Restricted'),('warn','Warning')],string="PR Control",default="restrict")
    restrict_allow_ledger = fields.Selection([('allow','Allow'),('restrict' , 'Restricted'),('warn','Warning')],string="Ledger Control",default="allow")
    planned_amount = fields.Float('Original Planned', required=True, digits=0)
    planned_changes_amount = fields.Float('Planned Changes', digits=0, compute="_compute_planned_amount_changes")
    planned_amount_sum = fields.Float('Planned Amount', digits=0, compute="_compute_planned_amount_sum")

    # commitment_amount = fields.Float(compute='_compute_commitment_amount', string='Commitment Amount', digits=0)
    requested_amount = fields.Float(digits=0, compute="_compute_budgeted_requested_amount") #, store=True)
    requested_amount_unbudget = fields.Float(digits=0, compute="_compute_unbudgeted_requested_amount") #, store=True)
    avail_req_amount = fields.Float(digits=0, compute="_compute_avail_req_amount", string="Available Amount")
    commitment_amount = fields.Float(digits=0, compute="_compute_practical_amount")
    available_amount = fields.Float(digits=0, compute="_compute_practical_amount", string="Available Amount")
    request_percentage = fields.Float(string='Achievement', compute='_compute_request_percentage', group_operator = 'avg')
    budget_request_ids = fields.One2many('budget.request.line', 'selected_budget_id', 'Requested List', copy=False)
    adjustment_line_ids = fields.One2many('budget.adjustment.line', 'budget_line_id', 'Adjustment List', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready'),
        ('close', 'Closed')
        ], 'Status', default='draft', readonly=True, track_visibility='always')
    group_id = fields.Many2one('account.budget.post.group', string="Budget Group", related='general_budget_id.group_id', store=True)
    budget_direction = fields.Selection([('income', 'Income'), ('cost', 'Cost / Expense')], string='Direction', related='group_id.direction')

    _fields_to_compute = ['commitment_amount', 'available_amount', 'planned_changes_amount',
                          'planned_amount_sum', 'requested_amount', 'requested_amount_unbudget',
                          'avail_req_amount', 'practical_amount', 'theoritical_amount']

    @api.multi
    def _compute_request_percentage(self):
        for line in self:
            if line.planned_amount_sum != 0.00:
                line.request_percentage = float((line.requested_amount or 0.0) / line.planned_amount_sum) * 100
            else:
                line.request_percentage = 0.00

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        print('View_id: %s, view_type: %s'%(view_id, view_type))
        res = super(BudgetLine, self).fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type == 'form':
            arch = etree.XML(res['arch'])
            button = arch.xpath("//button[@name='action_budget_to_adjust']")[0]
            button.set('invisible', self.env.context.get('budget_position') and '0' or '1')
            setup_modifiers(button)
            res['arch'] = etree.tostring(arch, encoding='utf-8')
        return res

    @api.multi
    def action_budget_to_adjust(self):
        budget_adjustment = self.env['budget.adjustment'].sudo().search([('id', '=', self.env.context.get('budget_adjustment_id'))])
        if self.env.context.get('budget_position') == 'adjust':
            budget_adjustment.budget_line_id_adj = self.id
            budget_adjustment.cost_center_id_adj = self.cost_center_id.id
            budget_adjustment.analytic_account_id_adj = self.analytic_account_id.id
            budget_adjustment.date_from_adj = self.date_from
            budget_adjustment.date_to_adj = self.date_to
            budget_adjustment.restrict_allow_adj = self.restrict_allow
            budget_adjustment.avail_req_amount_adj = self.avail_req_amount
        else:
            budget_adjustment.budget_line_id_src = self.id
            budget_adjustment.cost_center_id_src = self.cost_center_id.id
            budget_adjustment.analytic_account_id_src = self.analytic_account_id.id
            budget_adjustment.date_from_src = self.date_from
            budget_adjustment.date_to_src = self.date_to
            budget_adjustment.restrict_allow_src = self.restrict_allow
            budget_adjustment.avail_req_amount_src = self.avail_req_amount
        # return self.env.ref('account_budget_kopkarla.act_budget_adjustment_view').read()[0]
        # return self.env.context.get('action')
        view = self.env.ref('account_budget_kopkarla.view_account_budget_adjustment_form')
        budget_adjustment_id = self.env.context.get('budget_adjustment_id')
        return {
            'name': 'Budget Adjustment',
            'type': 'ir.actions.act_window',
            # 'view_type': 'form',
            # 'view_mode': 'tree,form',
            'res_model': 'budget.adjustment',
            'views': [(view.id, 'form')],
            # 'view_id': view.id,
            'target': 'current',
            'res_id': budget_adjustment_id,
            # 'limit': 5,
            # 'context': {'budget_adjustment_id': self.id,
            #             'budget_position': 'origin',
            #             'action': action},
        }

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            record_name = record.crossovered_budget_id.name + ' - ' + \
                          record.general_budget_id.name \
                          # + ' - ' + \
                          # record.cost_center_id.name + ' - ' + \
                          # record.analytic_account_id.name + ' - ' + \
                          # record.date_from + ' - ' + record.date_to
            result.append((record.id, record_name))
        return result

    @api.one
    def _compute_planned_amount_changes(self):
        change_amount = 0.0
        for lines in self.adjustment_line_ids:
            for line in lines:
                change_amount += line.amount
        self.planned_changes_amount = change_amount

    @api.multi
    @api.depends("planned_amount")
    def _compute_planned_amount_sum(self):
        for line in self:
            line.planned_amount_sum = line.planned_amount + line.planned_changes_amount

    @api.multi
    def _compute_budgeted_requested_amount(self):
        for line in self:
            result = 0.0
            for req in line.budget_request_ids:
                if (req.budget_request_id.state == 'done' and req.allow_unbudget == False):
                    result += req.requested_amount - req.released_amount
                elif (req.budget_request_id.state == 'release'):
                    result += req.requested_amount
            line.requested_amount = -result

    @api.multi
    def _compute_unbudgeted_requested_amount(self):
        for line in self:
            result = 0.0
            for req in line.budget_request_ids:
                if (req.budget_request_id.state == 'done' and req.allow_unbudget == True):
                    result += req.requested_amount
            line.requested_amount_unbudget = -result

    @api.multi
    def _compute_avail_req_amount(self):
        for line in self:
            line.avail_req_amount = (line.state == 'ready' and line.planned_amount_sum - line.requested_amount) or 0

    @api.multi
    def _compute_practical_amount(self):
        for line in self:
            practical_amount = commitment_amount = 0.0
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = self.env.context.get('wizard_date_to') or \
                line.date_to
            date_from = self.env.context.get('wizard_date_from') or \
                line.date_from
            if line.analytic_account_id.id:
                params = (line.analytic_account_id.id,
                          date_from, date_to, acc_ids,)
                self.env.cr.execute(
                    self._get_sql_query() +
                    "AND general_account_id=ANY(%s)", params)
                practical_amount = self.env.cr.fetchone()[0] or 0.0
                self.env.cr.execute(
                    self._get_sql_query() +
                    "AND commitment_account_id=ANY(%s)", params)
                commitment_amount = self.env.cr.fetchone()[0] or 0.0
            line.practical_amount = practical_amount
            line.commitment_amount = commitment_amount
            line.available_amount = line.planned_amount - \
                line.commitment_amount

    @api.multi
    def _compute_commitment_amount(self):
        for line in self:
            result = 0.0
            date_to = self.env.context.get('wizard_date_to') or line.date_to
            date_from = self.env.context.get('wizard_date_from') or line.date_from
            line.commitment_amount = 0
            purchase_res = self.env['purchase.order'].search([('date_order', '>=', date_from),
                                                              ('date_order', '<=', date_to),
                                                              # ('analytic_account_id', '=', line.analytic_account_id.id),
                                                              ('company_id', '=', line.company_id.id),
                                                              ('state', 'in', ['purchase', 'done'])])
            total_purch = 0
            for purchase in purchase_res:
                purch_line_res = self.env['purchase.order.line'].search([('order_id', '=', purchase.id),
                                                                         ('account_analytic_id', '=', line.analytic_account_id.id),
                                                                         ('cost_center_id', '=', line.cost_center_id.id)
                                                                         ])
                for purch_line in purch_line_res:
                    if purch_line.account_id.id in line.general_budget_id.account_ids.ids:
                        total_purch = total_purch - purch_line.price_subtotal
            line.commitment_amount = total_purch

    @api.model
    def _get_sql_query(self):
        return """
            SELECT SUM(amount)
            FROM account_analytic_line
            WHERE account_id=%s
                AND (date between to_date(%s,'yyyy-mm-dd')
                AND to_date(%s,'yyyy-mm-dd'))
        """

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        fields_to_compute = []
        for field in self._fields_to_compute:
            if field in fields:
                fields.remove(field)
                fields_to_compute.append(field)
        res = super(BudgetLine, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)
        if fields_to_compute:
            for group in res:
                if group.get('__domain'):
                    line_infos = self.search_read(group['__domain'],
                                                  fields_to_compute)
                    for field in fields_to_compute:
                        group[field] = sum([l[field] for l in line_infos])
        return res

    @api.multi
    def action_open_analytic_lines(self):
        self.ensure_one()
        return {
            'name': _('Analytic Lines'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line',
            'target': self._context.get('target', 'new'),
            'domain': [('id', 'in', self.analytic_line_ids._ids)],
            'context': self._context,
        }

    def _validate_sign_planned_amount(self):
        if self.planned_amount:
            if self.general_budget_id.sign == 'negative':
                if self.planned_amount > 0:
                    raise UserError('Planned amount of budget %s must be negative.' % self.general_budget_id.name)
            else:
                if self.planned_amount < 0:
                    raise UserError('Planned amount of budget %s must be positive.' % self.general_budget_id.name)
        # else:
        #     raise UserError('Planned amount of budget %s can not be zero.' % self.general_budget_id.name)

    @api.multi
    @api.onchange('planned_amount')
    def _onchange_planned_amount(self):
        if self.id:
            self._validate_sign_planned_amount()

    @api.onchange('general_budget_id')
    def _onchange_general_budget_id(self):
        self.cost_center_id = self.crossovered_budget_id.cost_center_id.id
        self.analytic_account_id = self.crossovered_budget_id.analytic_account_id.id

class BudgetPositionCommitmentLimit(models.Model):
    _name = 'account.budget.post.commitment_limit'
    _description = 'Budgetary Position Commitment Limit'
    _rec_name = 'budget_post_id'

    budget_post_id = fields.Many2one(
        'account.budget.post', 'Budgetary Position',
        required=True, index=True, ondelete='cascade')
    user_id = fields.Many2one(
        'res.users', 'User', required=True, index=True)
    amount_limit = fields.Float(
        'Commitment Amount Limit', digits=dp.get_precision('Account'),
        required=True)

    @api.one
    @api.constrains('amount_limit', 'user_id')
    def check_amount_limit_inferior_global_limit(self):
        if self.user_id.commitment_global_limit and \
                self.amount_limit > self.user_id.commitment_global_limit:
            raise UserError(_("You cannot define a budget post commitment "
                              "limit superior to the global limit of "
                              "this user"))

class BudgetPosition(models.Model):
    _inherit = 'account.budget.post'

    budget_type = fields.Selection([('asset','Asset'), ('ledger' , 'Ledger')], default="ledger")
    sign = fields.Selection([('positive','Positive'), ('negative' , 'Negative')], default="negative")
    commitment_limit_ids = fields.One2many(
        'account.budget.post.commitment_limit', 'budget_post_id',
        'Commitment Limits')
    budget_asset_ids = fields.Many2many('account.asset.category', 'account_budget_asset_rel', 'budget_position_id', 'asset_type_id', 'Budget Asset')
    group_id = fields.Many2one('account.budget.post.group', 'Budget Group', index=True, ondelete='restrict')

    @api.multi
    def name_get(self):
        self.read(['name', 'group_id', 'account_ids'])
        return [(template.id, '%s %s - %s' % (",".join([p.code for p in template.account_ids]), template.group_id.name, template.name)) for template in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """ search full name and barcode """
        if args is None:
            args = []
        recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def _check_account_ids(self, vals):
        # Raise an error to prevent the account.budget.post to have not specified account_ids.
        # This check is done on create because require=True doesn't work on Many2many fields.
        if 'account_ids' in vals:
            account_ids = self.resolve_2many_commands('account_ids', vals['account_ids'])
        else:
            account_ids = self.account_ids
        if 'budget_asset_ids' in vals:
            budget_asset_ids = self.resolve_2many_commands('budget_asset_ids', vals['budget_asset_ids'])
        else:
            budget_asset_ids = self.budget_asset_ids
        if 'budget_type' in vals:
            budget_type = vals['budget_type']
        else:
            budget_type = self.budget_type

        if budget_type == 'ledger':
            if not account_ids:
                raise ValidationError(_('The budget must have at least one account.'))
        else:
            if not budget_asset_ids:
                raise ValidationError(_('The budget must have at least one asset type.'))


class BudgetPositionGroup(models.Model):
    _name = 'account.budget.post.group'

    name = fields.Text(string="Group")
    direction = fields.Selection([('income', 'Income'), ('cost', 'Cost / Expense')])
    sign = fields.Selection([('positive','Positive'), ('negative' , 'Negative')])


class BudgetPositionList(models.Model):
    _name = "account.budget.post.list"
    _description = "Budgetary position list"
    _auto = False

    # company_id = fields.Many2one('res.company', 'Company')
    group_id = fields.Many2one('account.budget.post.group', 'Budget Group')
    account_id = fields.Many2one('account.account', 'Account')
    name = fields.Char('Name', required=True)
    sign = fields.Selection([('positive','Positive'), ('negative' , 'Negative')])
    budget_type = fields.Selection([('asset','Asset'), ('ledger' , 'Ledger')])

    @api.model_cr
    def init(self):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE OR REPLACE VIEW %s AS (
            select p.id, p.budget_type, a.account_id, p.name, p.group_id, p.sign
            from account_budget_post p inner join account_budget_rel a on p.id = a.budget_id
        )""" % self._table)

# class BudgetMonitoring(models.Model):
#     _name = "account.budget.monitoring"
#     _description = "Budget Monitoring"
#     _auto = False
#
#     general_budget_id = fields.Many2one('account.budget.post', required=True)
#     cost_center_id = fields.Many2one("cost.center", string='Cost Center') #, required=True)
#     analytic_line_ids = fields.One2many('account.analytic.line', 'budget_line_id', 'Analytic Lines', copy=False)
#     date_from = fields.Date('Start Date', required=True)
#     date_to = fields.Date('End Date', required=True)
#     planned_amount = fields.Float('Budget', required=True, digits=0)
#
#     @api.model_cr
#     def init(self):
#         # self._table = account_invoice_report
#         tools.drop_view_if_exists(self.env.cr, self._table)
#         self.env.cr.execute("""CREATE OR REPLACE VIEW %s AS (
#             select id, general_budget_id, cost_center_id, analytic_account_id, date_from, date_to, planned_amount
#             from crossovered_budget_lines
#             where state = 'ready'
#         )""" % self._table)