from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseRequestType(models.Model):
    _name = 'purchase.request.type'

    prod_categ_id = fields.Many2one('product.category', 'Product Category')
    account_trade_request_id = fields.Many2one('account.account', 'Trading Account')
    account_datacom_request_id = fields.Many2one('account.account', 'Datacom Account')
    account_overhead_request_id = fields.Many2one('account.account', 'Overhead Account')


class SprogroupPurchaseRequest(models.Model):

    _inherit = 'sprogroup.purchase.request'

    request_type = fields.Selection([
        ('trade', 'Trading'),
        ('datacom', 'Datacom'),
        ('overhead', 'Overhead'),
    ], 'Request Type', readonly=True, states={'draft': [('readonly', False)]})
    account_id = fields.Many2one('account.account', 'Account Ledger', compute='_set_account_id')
    allow_on_behalf_of = fields.Boolean('Allow On Behalf Of', compute='_set_allow_on_behalf_of')
    on_behalf_of = fields.Many2one('hr.employee', 'On Behalf Of') #, domain=lambda self: self._get_employee_mapping())
    department_id = fields.Many2one('hr.department', string='Department', compute='_compute_department', store=True,)

    # active_budget_count = fields.Integer(
    #     string='Active Budget',
    #     compute='_compute_active_budget_count',
    # )
    #
    # def _compute_active_budget_count(self):
    #     budget_model = self.env['crossovered.budget.lines']
    #     # today = fields.Date.today()
    #     fetch_data = budget_model.read_group([
    #             ('state', '=', 'ready'),
    #             ('cost_center_id', '=', self.cost_center_id.id),
    #             ('analytic_account_id', '=', self.analytic_account_id.id),
    #         ],
    #         [],
    #         [],
    #         lazy=False)
    #     result = [data['__count'] for data in fetch_data]
    #     self.active_budget_count = str(result[0])
    #
    # def show_available_budget(self):
    #     view = self.env.ref('account_budget_kopkarla.view_account_budget_available_tree')
    #     # form = self.env.ref('account_budget_kopkarla.view_account_budget_available_form')
    #     search_view = self.env.ref('account_budget_kopkarla.view_account_budget_available_search')
    #
    #     # context = {'budget_adjustment_id': self.id,
    #     #             'budget_position': self.env.context.get('budget_position'),
    #     #         }
    #     domain = [('state', '=', 'ready')]
    #     if self.cost_center_id:
    #         domain.append(('cost_center_id', '=', self.cost_center_id.id))
    #     if self.analytic_account_id:
    #         domain.append(('analytic_account_id', '=', self.analytic_account_id.id))
    #
    #         # context.update({'cost_center_adj': self.cost_center_id_adj.id})
    #         # context.update({'analytic_account_adj': self.analytic_account_id_adj.id})
    #     return {
    #         'name': 'Available Budgets',
    #         'type': 'ir.actions.act_window',
    #         # 'view_type': 'form',
    #         # 'view_mode': 'tree,form',
    #         'res_model': 'crossovered.budget.lines',
    #         'views': [(view.id, 'tree')], #(form.id, 'form')],
    #         # 'view_id': view.id,
    #         'target': 'current',
    #         'search_view_id': search_view.id,
    #         # 'limit': 5,
    #         'domain': domain,
    #         # 'context': context,
    #     }

    @api.one
    @api.depends('requested_by', 'on_behalf_of')
    def _compute_department(self):
        if (self.requested_by.id == False):
            self.department_id = None
            return

        employee = self.on_behalf_of or self.env['hr.employee'].search([('work_email', '=', self.requested_by.email)])
        if (len(employee) > 0):
            self.department_id = employee[0].department_id.id
            self.cost_center_id = employee[0].cost_center_id.id
            self.analytic_account_id = employee[0].analytic_account_id.id
        else:
            self.department_id = None
            self.cost_center_id = None
            self.analytic_account_id = None

    @api.multi
    @api.onchange('requested_by')
    def _set_allow_on_behalf_of(self):
        on_behalf_of = self.env['purchase.request.employee.mapping'].sudo().search([('requested_by', '=', self.requested_by.id)])
        self.allow_on_behalf_of = len(on_behalf_of.mapped('on_behalf_of').ids) > 0

        res = {}
        if self.allow_on_behalf_of:
            domain = {'on_behalf_of': [('id', 'in', on_behalf_of.mapped('on_behalf_of').ids)]}
            return {'domain': domain}
        return res

    @api.one
    def _set_account_id(self):
        for pr in self:
            for line in pr.line_ids:
                if line.account_id.id:
                    self.account_id = line.account_id.id
                    break

    @api.onchange('request_type', 'salesorder_id')
    def _get_account_id(self):
        if self.salesorder_id.id:
            if self.salesorder_id.proj_type and self.salesorder_id.proj_type.project_account_id:
                project_expense_id = self.salesorder_id.proj_type.project_account_id.id
                for line in self.line_ids:
                    line.account_id = project_expense_id and project_expense_id or line.product_id.categ_id.property_account_expense_categ_id.id
            else:
                for line in self.line_ids:
                    line.account_id = line.product_id.categ_id.property_account_expense_categ_id.id
        else:
            for line in self.line_ids:
                category_id = line.product_id.categ_id
                request_type = self.env['purchase.request.type'].sudo().search([('prod_categ_id', '=', category_id.id)], limit=1)
                if not request_type.id:
                    while not request_type.id:
                        category_id = category_id.parent_id
                        request_type = self.env['purchase.request.type'].sudo().search([('prod_categ_id', '=', category_id.id)], limit=1)
                account_id = False
                if request_type.id:
                    if self.request_type == 'trade':
                        account_id = request_type.account_trade_request_id.id
                    elif self.request_type == 'datacom':
                        account_id = request_type.account_datacom_request_id.id
                    elif self.request_type == 'overhead':
                        account_id = request_type.account_overhead_request_id.id
                if not account_id:
                    # line.account_id = line.product_id.categ_id.property_account_expense_categ_id.id
                    # account_id = line.product_id.categ_id.property_account_expense_categ_id.id
                    if line.product_id.id:
                        accounts_data = line.product_id.product_tmpl_id.get_product_accounts()
                        if line.product_id.type == 'product':
                            account_id = accounts_data['stock_valuation'].id
                            # account_id = accounts_data['expense'].id
                        else:
                            account_id = accounts_data['expense'].id
                        # line.account_id = account_id
                line.account_id = account_id


class SprogroupPurchaseRequestLine(models.Model):
    _inherit = "sprogroup.purchase.request.line"

    account_id = fields.Many2one('account.account', 'Account Ledger', store=True, compute='_get_account_id') #, required=True)
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('purchase_ok', '=', True)], required=True,
        track_visibility='onchange')

    @api.onchange('product_id')
    def _get_account_id(self):
        if self.request_id.salesorder_id.id:
            if self.request_id.salesorder_id.proj_type and self.request_id.salesorder_id.proj_type.project_account_id:
                project_expense_id = self.request_id.salesorder_id.proj_type.project_account_id.id
                self.account_id = project_expense_id and project_expense_id or self.product_id.categ_id.property_account_expense_categ_id.id
            else:
                self.account_id = self.product_id.categ_id.property_account_expense_categ_id.id
        elif self.product_id.id:
            category_id = self.product_id.categ_id
            request_type = self.env['purchase.request.type'].sudo().search([('prod_categ_id', '=', category_id.id)], limit=1)
            if request_type.id:
                while not request_type.id:
                    category_id = category_id.parent_id
                    request_type = self.env['purchase.request.type'].sudo().search([('prod_categ_id', '=', category_id.id)], limit=1)
            if request_type.id:
                if self.request_id.request_type == 'trade':
                    request_expense_id = request_type.account_trade_request_id.id
                elif self.request_id.request_type == 'datacom':
                    request_expense_id = request_type.account_datacom_request_id.id
                else: # self.request_id.request_type == 'overhead':
                    request_expense_id = request_type.account_overhead_request_id.id
                # else:
                #     request_expense_id = False
                if not request_expense_id:
                    request_expense_id = self.product_id.categ_id.property_account_expense_categ_id.id
                self.account_id = request_expense_id
            else:
                if self.product_id.id:
                    account_id = False
                    accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
                    if self.product_id.type == 'product':
                        if accounts_data['stock_valuation']:
                            account_id = accounts_data['stock_valuation'].id
                        else:
                            raise UserError(
                                _('Stock account is not set for product %s') % self.product_id.name
                            )
                    else:
                        if accounts_data['expense']:
                            account_id = accounts_data['expense'].id
                        else:
                            raise UserError(
                                _('Expense account is not set for product %s') % self.product_id.name
                            )
                    self.account_id = account_id


class purchase_request_employees_mapping(models.Model):
    _name = 'purchase.request.employee.mapping'
    _description = 'Purchase Request Employee Mapping'

    requested_by = fields.Many2one('res.users', 'Requested by', required=True,)
    on_behalf_of = fields.Many2one('hr.employee', 'On Behalf Of', required=True)

    _sql_constraints = [
        ('purchase_request_employee_mapping_unique',
         'unique (requested_by, on_behalf_of)',
         'Choose another value - it has to be unique!')
    ]
