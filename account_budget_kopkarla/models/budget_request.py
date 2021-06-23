from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
# from lxml import etree
# from odoo.osv.orm import setup_modifiers
# from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
# from odoo.http import request


class BudgetRequest(models.Model):
    _name = "budget.request"
    _description = "Budget Request Table"
    # _order = "date desc, id desc"

    # READONLY_STATES = {
    #     'draft': [('readonly', False)],
    #     'done': [('readonly', True)],
    #     'cancel': [('readonly', True)],
    # }

    name = fields.Char(string='Name', index=True, required=True,
                       readonly=True, states={'draft': [('readonly', False)]},
                       help='The name that will be used on budget request control')
    date = fields.Datetime('Date', required=True, index=True, copy=False, default=fields.Datetime.now,
                           readonly=True, states={'draft': [('readonly', False)]},)
    description = fields.Text('Description', readonly=True, states={'draft': [('readonly', False)]},)
    origin = fields.Selection([('purchase_request', 'Purchase Request'),], readonly=True, required=True, default='purchase_request')
    request_id = fields.Many2one('sprogroup.purchase.request', 'Purchase Request', ondelete='cascade', readonly=True)
    line_ids = fields.One2many('budget.request.line', 'budget_request_id', string='Budget Lines', copy=True,
                               readonly=True, states={'draft': [('readonly', False)]},)
    margin_ids = fields.One2many('budget.request.margin', 'budget_request_id', string='Proyeksi Margin', copy=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft')
    show_force_approval = fields.Boolean('Show Force Approval')
    sale_order_id = fields.Many2one('sale.order', string='SO Number', readonly=True) # salesorder_id
    sale_confirm_date = fields.Datetime(string='Confirmation Date', readonly=True) # confirmation_date
    sale_delivery_doc = fields.Date(string='Delivery Date', readonly=True) # delivery_doc
    sale_area_kode = fields.Many2one('enhanced.sales.area', string='Sales Area', readonly=True) # sales_area_kode
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    sale_amount_total = fields.Monetary(string='Total', readonly=True) # amount_total
    allow_unbudget = fields.Boolean(string="Allow Unbudget", readonly=True, states={'draft': [('readonly', False)]},)
    nojar = fields.Char(string='Nomor Jaringan', readonly=True)
    proj_type = fields.Many2one('enhanced.sales.project.tabel', string='Jenis Project', readonly=True)
    ord_type = fields.Many2one('enhanced.sales.jenis.tabel', string='Jenis Order', readonly=True)
    pek_type = fields.Many2one('enhanced.sales.pekerjaan.tabel', string='Jenis Pekerjaan', readonly=True)
    show_asset_budget = fields.Boolean('Show Asset Budget')

    @api.multi
    def budget_request_approve_action(self):
        msg = ''
        is_approved = True
        if self.env.context.get('force') == 0:
            for req in self.line_ids:
                if req.restrict_allow != 'allow':
                    if req.requested_amount > req.available_budget:
                        msg = (req.selected_budget_id and '%sRequested amount on %s is larger than available budget.\n' % (msg, req.budget_account_id.name)) or \
                              '%sAccount %s has no budget selected.\n' % (msg, req.budget_account_id.name)
                        if req.restrict_allow == 'restrict' or not req.selected_budget_id:
                            is_approved = False

        if is_approved:
            self.date = datetime.now()
            self.state = 'done'
            self.request_id.budget_request_id = self.id
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
    _name = "budget.request.line"
    _description = "Budget Request Lines"
    _rec_name = "selected_budget_id"

    budget_request_id = fields.Many2one('budget.request', string='Budget Request', index=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=1)
    purchase_request_line_ids = fields.One2many('sprogroup.purchase.request.line', 'budget_request_line_id', 'Purchase Request Lines', readonly=True)
    # name = fields.Text(string='Description')
    budget_account_id = fields.Many2one('account.account', 'Budget Account', readonly=True)
    income_account_id = fields.Many2one('account.account', 'Income Account', readonly=True)
    cost_center_id = fields.Many2one("cost.center", string='Cost Center', ondelete="cascade", readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete="cascade", readonly=True)
    requested_amount = fields.Float(string='Requested Amount', readonly=True)
    selected_budget_id = fields.Many2one('crossovered.budget.lines', string='Selected Budget', ondelete="cascade", readonly=True)
    available_budget = fields.Float(string='Available Budget', readonly=True)
    restrict_allow = fields.Selection([('allow','Allow'),('restrict' , 'Restricted'),('warn','Warning')],string="Budget Control", readonly=True)
    allow_unbudget = fields.Boolean(string="Allow Unbudget", related='budget_request_id.allow_unbudget')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', compute='_get_budget_state', method=True)
    asset_options = fields.Selection([('asset', 'Asset'),
                                      ('inventory', 'Inventory')], 'Budget Type')

    @api.one
    def _get_budget_state(self):
        self.state = self.budget_request_id.state

    @api.onchange('asset_options')
    def _onchange_asset_option(self):
        if self.asset_options == 'asset':
            budget_request = self.env['budget.request'].search([('request_id', '=', self.budget_request_id.request_id.id)])
            for line in budget_request.line_ids:
                if line.budget_account_id == self.budget_account_id:
                    requested_amount_org = line.requested_amount_org
            msg = ''
            asset_category = False
            for line in self.budget_request_id.request_id.line_ids:
                asset_category = line.product_id.asset_category_id
                if not asset_category.id:
                    msg = '%s\nProduct %s belum di set asset category.' % (msg, line.product_id.name)
            if msg:
                raise UserError(msg)
            if asset_category.method_number:
                self.requested_amount = self._get_original_request_amount(self.budget_account_id) # / asset_category.method_number
                # self.budget_account_id = asset_category.account_depreciation_expense_id.id
                self.budget_account_id = asset_category.account_asset_id.id
        else:
            asset_category = False
            requested_amount = 0
            for line in self.budget_request_id.request_id.line_ids:
                if line.product_id.asset_category_id.id:
                    self.budget_account_id = line.account_id
                    requested_amount += line.subtotal

            self.requested_amount = requested_amount
        self.budget_request_id._onchange_date()

    def _get_original_request_amount(self, account_id):
        requested_amount = 0
        for line in self.budget_request_id.request_id.line_ids:
            if line.account_id.id == account_id.id:
                requested_amount += line.subtotal
        return requested_amount


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


class BudgetRequestMargin(models.Model):
    _name = "budget.request.margin"

    budget_request_id = fields.Many2one('budget.request', string='Budget Request', index=True, ondelete='cascade')
    name = fields.Char(string='Documents', index=True, required=True, readonly=True)
    amount = fields.Float(string='Total', readonly=True)
    state = fields.Char(string='Status', readonly=True)


# class BudgetRequestLinePosition(models.Model):
#     _name = "budget.request.line.position"
#     _rec_name = "budget_position_id"
#     _description = "Budget Request Line Position"
#
#     budget_request_line_id = fields.Many2one('budget.request.line', string='Budget Request Line', index=True, required=True, ondelete='cascade')
#     budget_line_id = fields.Many2one('crossovered.budget.lines', string='Budget Available', ondelete="cascade")


class BudgetRequestReport(models.TransientModel):
    _name = "budget.request.report"
    _order = 'date, request_id'

    request_id = fields.Many2one('sprogroup.purchase.request', 'Purchase Request', ondelete='cascade', readonly=True)
    date = fields.Date('Date', index=True)
    cost_center_id = fields.Many2one("cost.center", string='Cost Center', ondelete="cascade", readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete="cascade", readonly=True)
    account_id = fields.Many2one('account.account', 'Budget Account', readonly=True)
    budget_request_line_id = fields.Many2one('budget.request.line', string='Budget Request Line', index=True, ondelete='cascade')
    request_amount = fields.Float(string='Request Amount', readonly=True)
    budget_amount = fields.Float(string='Budget Amount', readonly=True)
    unbudget = fields.Boolean(string="Unbudget", readonly=True)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # print('View_id: %s, view_type: %s'%(view_id, view_type))
        res = super(BudgetRequestReport, self).fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type == 'tree':
            # arch = etree.XML(res['arch'])
            # button = arch.xpath("//button[@name='action_budget_to_adjust']")[0]
            # button.set('invisible', self.env.context.get('budget_position') and '0' or '1')
            # setup_modifiers(button)
            # res['arch'] = etree.tostring(arch, encoding='utf-8')
            self.populate_budget_request()
        return res

    @api.multi
    def populate_budget_request(self):
        query = """
            delete from budget_request_report where create_uid = %s;
            select a.*, brl.available_budget, br.allow_unbudget
            from (
                select pr.id,
                       pr.date_start,
                       pr.cost_center_id,
                       pr.analytic_account_id,
                       prl.account_id,
                       prl.budget_request_line_id,
                       sum(prl.product_qty * prl.cost_product) as request_amount
                from sprogroup_purchase_request_line prl
                         inner join sprogroup_purchase_request pr on prl.request_id = pr.id
                where pr.state in ('leader_request', 'leader_approved', 'done')
                      and pr.date_start >= '1 Jan 2021' --and br.allow_unbudget = False
                group by pr.id, pr.date_start, pr.cost_center_id, pr.analytic_account_id,
                      prl.account_id, prl.budget_request_line_id--, br.allow_unbudget, br.id
            ) a left join budget_request_line brl on a.budget_request_line_id = brl.id
                left join budget_request br on brl.budget_request_id = br.id
        """
        cr = self.env.cr
        params = (self.env.user.id,)
        cr.execute(query, params)
        res = cr.fetchall()

        for r in res:
            line = self.env['budget.request.report']
            account_id = r[4] != 'None' and r[4] or False
            if r[5] != 'None' and account_id:
                brl_id = self.env['budget.request.line'].sudo().browse(r[5]).id
                if not brl_id:
                    brl_id = self.env['budget.request.line'].sudo().search([('budget_request_id', '=', r[0]), ('budget_account_id', '=', account_id)]).id
            else:
                brl_id = False
            line.create({
                'request_id': r[0],
                'date': r[1],
                'cost_center_id': r[2] != 'None' and r[2] or False,
                'analytic_account_id': r[3] != 'None' and r[3] or False,
                'account_id': account_id,
                'budget_request_line_id': brl_id,
                'request_amount': r[6],
                'budget_amount': r[7],
                'unbudget': r[8],
            })