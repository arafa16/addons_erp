from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class PurchaseRequest(models.Model):
    _inherit = 'sprogroup.purchase.request'
    _order = 'name DESC'

    sales_delivery_doc = fields.Date(string='Delivery Date', related='salesorder_id.delivery_doc')
    sales_amount_total = fields.Monetary(string='Sales Total', related='salesorder_id.amount_total')
    currency_id = fields.Many2one("res.currency", related='salesorder_id.currency_id', string="Currency")
    sales_state = fields.Selection(string='Status', related='salesorder_id.state')
    coannya = fields.Many2one('account.account', string='Chart of Account', compute='get_account_id')

    budget_request_id = fields.Many2one('budget.request', 'Budget Request', ondelete='set null', readonly=True)
    active_budget_count = fields.Integer(string='Active Budget', compute='_compute_active_budget_count',)

    def show_selected_budget(self):
        budget_approval_view_id = self.env.ref('account_budget_kopkarla.account_budget_approval_form')
        # domain = [('id', '=', self.budget_request_id.id)]
        return {
            'name': _('Budget Approval'),
            'res_model': 'budget.request',
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',  # 'form',
            'view_mode': 'form',
            'view_id': budget_approval_view_id.id,
            'target': 'new',  # 'current', #
            'res_id': self.budget_request_id.id,
            # 'domain': domain,
        }

    def _compute_active_budget_count(self):
        for pr in self:
            budget_model = self.env['crossovered.budget.lines']
            # today = fields.Date.today()
            fetch_data = budget_model.read_group([
                    ('state', '=', 'ready'),
                    ('cost_center_id', '=', pr.cost_center_id.id),
                    ('analytic_account_id', '=', pr.analytic_account_id.id),
                ],
                [],
                [],
                lazy=False)
            result = [data['__count'] for data in fetch_data]
            pr.active_budget_count = str(result[0])

    def show_available_budget(self):
        view = self.env.ref('account_budget_kopkarla.view_account_budget_available_tree')
        # form = self.env.ref('account_budget_kopkarla.view_account_budget_available_form')
        search_view = self.env.ref('account_budget_kopkarla.view_account_budget_available_search')

        context = {'group_by': 'general_budget_id'}
        # context = {'budget_adjustment_id': self.id,
        #             'budget_position': self.env.context.get('budget_position'),
        #         }
        domain = [('state', '=', 'ready')]
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
            'views': [(view.id, 'tree')], #(form.id, 'form')],
            # 'view_id': view.id,
            'target': 'current',
            'search_view_id': search_view.id,
            # 'limit': 5,
            'domain': domain,
            'context': context,
        }

    @api.one
    def get_account_id(self):
        project_expense_id = False
        if self.salesorder_id and self.salesorder_id.proj_type and self.salesorder_id.proj_type.project_account_id:
            project_expense_id = self.salesorder_id.proj_type.project_account_id.id
        i = 0
        expense_account_id = False
        for line in self.line_ids:
            expense_account_id = project_expense_id and project_expense_id or line.product_id.categ_id.property_account_expense_categ_id.id
            if expense_account_id:
                break
        self.coannya = expense_account_id

    def request_budget_create(self):
        budget_request_id = self.env['budget.request'].search([('request_id', '=', self.id)])
        if budget_request_id:
            budget_request_id.line_ids.unlink()
        else:
            budget_request = {
                'name': 'Budget Request {}'.format(self.name),
                'date': datetime.now(),
                # 'description': '',
                'origin': 'purchase_request',
                'request_id': self.id,
                'state': 'draft',
                'sale_order_id': self.salesorder_id.id,
                'sale_confirm_date': self.salesorder_id.confirmation_date,
                'sale_delivery_doc': self.salesorder_id.delivery_doc,
                'sale_area_kode': self.salesorder_id.sales_area_kode.id,
                'nojar': self.salesorder_id.nojar,
                'proj_type': self.salesorder_id.proj_type.id,
                'ord_type': self.salesorder_id.ord_type.id,
                'pek_type': self.salesorder_id.pek_type.id,
                'sale_amount_total': self.salesorder_id.amount_total,
                'currency_id': self.salesorder_id.currency_id.id,
            }
            budget_request_id = self.env['budget.request'].create(budget_request)
            if self.salesorder_id:
                budget_request_margin = {
                    'budget_request_id': budget_request_id.id,
                    'name': self.salesorder_id.name,
                    'amount': self.salesorder_id.amount_untaxed,
                    'state': dict(self.env['sale.order'].fields_get(allfields=['state'])['state']['selection'])[self.salesorder_id.state]
                }
                margin = self.salesorder_id.amount_untaxed
                self.env['budget.request.margin'].create(budget_request_margin)
                purchase_requests = self.env['sprogroup.purchase.request'].sudo().search([('salesorder_id', '=', self.salesorder_id.id),
                                                                                          ('state', '!=', 'rejected')])
                for pr in purchase_requests:
                    budget_request_margin = {
                        'budget_request_id': budget_request_id.id,
                        'name': pr.name,
                        'amount': pr.amount_total,
                        'state': dict(self.env['sprogroup.purchase.request'].fields_get(allfields=['state'])['state']['selection'])[pr.state]
                    }
                    margin -= pr.amount_total
                    self.env['budget.request.margin'].create(budget_request_margin)
                budget_request_margin = {
                    'budget_request_id': budget_request_id.id,
                    'name': 'M A R G I N',
                    'amount': margin,
                    'state': '< < < < < < < < < < = = = = = = = = = = = = = = =',
                }
                self.env['budget.request.margin'].create(budget_request_margin)

        show_force_button = self.env['ir.config_parameter'].sudo().get_param('allow_force_budget_approve')
        budget_request_id.update({'show_force_approval': show_force_button})
        budget_request_lines = []
        project_expense_id = False
        if self.salesorder_id and self.salesorder_id.proj_type and self.salesorder_id.proj_type.project_account_id:
            project_expense_id = self.salesorder_id.proj_type.project_account_id.id
        i = 0
        # budget_request_line = {}
        set_asset_option = False
        for line in self.line_ids:
            # expense_account_id = project_expense_id and project_expense_id or line.product_id.categ_id.property_account_expense_categ_id.id
            expense_account_id = line.account_id.id
            requested_amount = 0
            for bl in budget_request_lines:
                if bl['budget_account_id'] == expense_account_id:
                    requested_amount = bl['requested_amount'] + line.subtotal
                    bl.update({'requested_amount': requested_amount,})
                    break
            if requested_amount == 0:
                budget_request_line = {
                    'budget_request_id': budget_request_id.id,
                    'budget_account_id': expense_account_id,
                    'income_account_id': self.salesorder_id.proj_type.id and self.salesorder_id.proj_type.project_income_id.id or line.product_id.categ_id.property_account_income_categ_id.id,
                    'cost_center_id': self.cost_center_id.id,
                    'analytic_account_id': self.analytic_account_id.id,
                    'requested_amount': line.subtotal,
                }
                budget_request_lines += [budget_request_line]
                accounts_data = line.product_id.product_tmpl_id.get_product_accounts()
                if line.product_id.type == 'product':
                    if accounts_data['stock_valuation']:
                        if expense_account_id == accounts_data['stock_valuation'].id:
                            set_asset_option = True
        budget_request_id.update({'show_asset_budget': set_asset_option})

        for budget_request_line in budget_request_lines:
            i += 1
            criteria = [('date_from', '<=', budget_request_id.date), ('date_to', '>=', budget_request_id.date)]
            general_budget_ids = self.env['account.budget.post'].search([('account_ids', '=', budget_request_line['budget_account_id'])])
            budget_ids = []
            for general_budget_id in general_budget_ids:
                budget_ids.append(general_budget_id.id)
            if budget_ids:
                criteria.append(('general_budget_id', 'in', budget_ids))
                if budget_request_line['cost_center_id']:
                    criteria.append(('cost_center_id', '=', budget_request_line['cost_center_id']))
                if budget_request_line['analytic_account_id']:
                    criteria.append(('analytic_account_id', '=', budget_request_line['analytic_account_id']))
                appropriate_budgets = self.env['crossovered.budget.lines'].search(criteria)
                if appropriate_budgets:
                    for appropriate_budget in appropriate_budgets:
                        if appropriate_budget.crossovered_budget_id.state == 'validate':
                            budget_request_line['sequence'] = i
                            budget_request_line['selected_budget_id'] = appropriate_budget.id
                            budget_request_line['available_budget'] = -appropriate_budget.avail_req_amount
                            budget_request_line['restrict_allow'] = appropriate_budget.restrict_allow
                            break
                else:
                    budget_request_line['sequence'] = i
            else:
                budget_request_line['sequence'] = i

            budget_request_line_saved = self.env['budget.request.line'].create(budget_request_line)
            for line in self.line_ids:
                if line.account_id == budget_request_line_saved.budget_account_id:
                    line.budget_request_line_id = budget_request_line_saved.id

    @api.multi
    def button_action_request_budget_confirm(self):
        budget_request_id = self.env['budget.request'].search([('request_id', '=', self.id)])
        budget_approval_view_id = self.env.ref('account_budget_kopkarla.account_budget_approval_form')
        return {
            'name': _('Budget Approval'),
            'res_model': 'budget.request',
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form', #'form',
            'view_mode': 'form',
            'view_id': budget_approval_view_id.id,
            'target': 'new', #'current', #
            'res_id': budget_request_id.id,
        }

    @api.multi
    def button_action_request_budget_check(self):
        super(PurchaseRequest, self).button_action_request_budget_check()
        self.request_budget_create()

    def request_budget_approval(self):
        if self.assigned_to.id == self._uid:
            tujuan = []
            if self.required5 == True:
                teksmail = self.penandatangan5.user_id.email
                tail = 'Ketua Pengurus'
                self.loa_request = 5
            if self.required4 == True:
                teksmail = self.penandatangan4.user_id.email
                tail = 'Pengurus/Direktur'
                self.loa_request = 4
            if self.required3 == True:
                teksmail = self.penandatangan3.user_id.email
                tail = 'General Manager'
                self.loa_request = 3
            if self.required2 == True:
                teksmail = self.penandatangan2.user_id.email
                tail = 'Manager'
                self.loa_request = 2
            if self.required1 == True:
                teksmail = self.penandatangan1.user_id.email
                tail = 'Asisten Manager'
                self.loa_request = 1
            tujuan.append(teksmail)
            template = 'purchase_request_loa'
            self.setConfirmLoA = True
            self.apvteks = tail
            self.state = 'leader_request'
            self._sent_mail(tujuan, template,tail)
        else:
            raise UserError('Access Denied')

    def remove_budget(self):
        if self.state in ('rejected', 'draft'):
            self.env['budget.request'].search([('request_id', '=', self.id)]).unlink()

    @api.multi
    def button_action_request_procure_reject(self):
        super(PurchaseRequest, self).button_action_request_procure_reject()
        self.remove_budget()

    @api.multi
    def button_action_assman_rejected(self):
        super(PurchaseRequest, self).button_action_assman_rejected()
        self.remove_budget()

    @api.multi
    def button_action_request_budget_reject(self):
        super(PurchaseRequest, self).button_action_request_budget_reject()
        self.remove_budget()

    @api.multi
    def button_action_request_loa_reject(self):
        super(PurchaseRequest, self).button_action_request_loa_reject()
        self.remove_budget()

    def validate_request(self):
        if not self.line_ids:
            raise UserError('Request line is empty.')
        for line in self.line_ids:
            if not line.subtotal:
                raise UserError('Line "%s" does not have amount.' % line.product_id.name)

    @api.multi
    def button_action_assman_check(self):
        self.validate_request()
        super(PurchaseRequest, self).button_action_assman_check()

    @api.multi
    def unlink(self):
        if self.state not in ['rejected', 'draft']:
            raise UserError(_('You cannot delete a document in %s state.\nDelete permitted in draft or rejected state.') % (self.state))
        return super(PurchaseRequest, self).unlink()

    @api.multi
    def make_bidding(self):
        super(PurchaseRequest, self).make_bidding()
        tender = self.env['purchase.requisition'].search([('nomor_pr', '=', self.id)], limit=1)
        if tender:
            tender.cost_center_id = self.cost_center_id.id
            tender.account_analytic_id = self.analytic_account_id.id
            for line in tender.line_ids:
                line.cost_center_id = self.cost_center_id.id
                line.account_analytic_id = self.analytic_account_id.id


class PurchaseRequestLine(models.Model):
    _inherit = "sprogroup.purchase.request.line"

    account_id = fields.Many2one('account.account') #, string='Account', compute='_get_invoice_line_account', store=True)
    budget_request_line_id = fields.Many2one('budget.request.line', string='Budget', readonly=True, ondelete='set null')
    state = fields.Selection(related='request_id.state', store=True)
    # coannya = fields.Many2one('account.account', string='Chart of Account', related='request_id.coannya', store=True)

    _fields_to_compute = ['subtotal']

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        fields_to_compute = []
        for field in self._fields_to_compute:
            if field in fields:
                fields.remove(field)
                fields_to_compute.append(field)
        res = super(PurchaseRequestLine, self).read_group(
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
    def write(self, vals):
        res = super(PurchaseRequestLine, self).write(vals)
        return res

    # @api.one
    # @api.depends('product_id')
    # def _get_invoice_line_account(self):
    #     if self.product_id:
    #         accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
    #         if self.product_id.type == 'product':
    #             # account_id = accounts_data['stock_valuation'].id
    #             account_id = accounts_data['expense'].id
    #         else:
    #             account_id = accounts_data['expense'].id
    #         self.account_id = account_id
