# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class HrExpense(models.Model):
    _inherit = "hr.expense"
    
    @api.depends('advance_expense_id', 'advance_expense_id.total_amount')
    def _compute_advance_expense_id(self):
        for rec in self:
            amount = 0.0
            amount = rec.advance_expense_id.total_amount
            rec.advance_amount = amount
            rec.variance_amount = rec.total_amount - amount

    name = fields.Char(string='Expense Description', readonly=False, required=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string="Employee", related='sheet_id.employee_id', store=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=False, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, domain=[('can_be_expensed', '=', True)], required=True)
    date = fields.Date(string="Expense Date", related='sheet_id.report_date', store=True,)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=False, related='sheet_id.currency_id', default=lambda self: self.company_id.currency_id)
    unit_amount = fields.Float(string='Unit Price', readonly=False, required=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, digits=dp.get_precision('Product Price'))
    quantity = fields.Float(required=True, readonly=False, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, digits=dp.get_precision('Product Unit of Measure'), default=1)
    total_amount = fields.Float(string='Expense Amount', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
    advance_expense_id = fields.Many2one('hr.advance.line', string='Cash Advance', copy=False, store=True)
    advance_amount = fields.Float(string='Advance Amount', compute='_compute_advance_expense_id', store=True, digits=dp.get_precision('Account'))
    variance_amount = fields.Float(string='Variance', digits=dp.get_precision('Account'), store=True)
    advance_currency_id = fields.Many2one('res.currency', string='Expense Advance Currency', related='advance_expense_id.currency_id', store=True,)
    cost_center_id = fields.Many2one('cost.center', required=False, string="Cost Center", related='sheet_id.cost_center_id', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', required=False, string='Analytic Account', related='sheet_id.analytic_account_id', store=True)
    sheet_id = fields.Many2one('hr.expense.sheet', string="Expense Report", readonly=True, copy=False, ondelete="cascade")
    payment_mode = fields.Selection([
        ("own_account", "Employee"),
        ("company_account", "Company")
    ], default='own_account', states={'done': [('readonly', True)], 'post': [('readonly', True)], 'submitted': [('readonly', True)]}, related='sheet_id.payment_mode', string="Payment By")
    tax_ids = fields.Many2many('account.tax', 'expense_tax', 'expense_id', 'tax_id', string='Taxes', states={'done': [('readonly', True)], 'post': [('readonly', True)]})
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', related='sheet_id.bank_journal_id')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''
            self.unit_amount = self.product_id.price_compute('standard_price')[self.product_id.id]
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account
            self.employee_id = self.sheet_id.employee_id.id
            self.cost_center_id = self.sheet_id.cost_center_id.id
            self.analytic_account_id = self.sheet_id.analytic_account_id.id

    @api.multi
    def submit_expenses(self): # Override Odoo method.
        result = super(HrExpense, self).submit_expenses()
        for rec in self:
            if rec.advance_expense_id:
                rec.advance_expense_id.reambursment = True
        return result

    @api.onchange('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            expense.untaxed_amount = expense.unit_amount * expense.quantity
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id,
                                                expense.quantity, expense.product_id,
                                                expense.sheet_id.partner_id)
            expense.total_amount = taxes.get('total_included')
            if expense.advance_expense_id:
                expense.variance_amount = expense.total_amount - expense.advance_amount

    @api.multi
    def _pay_move_line_get(self, payment_id):
        account_move = []
        for expense in self:
            move_line = expense._prepare_move_line_value()
            move_line['name'] = '%s: %s' % (expense.sheet_id.name, expense.name.split('\n')[0][:64])
            # if 'cost_center_id' in expense:
            #     move_line['cost_center_id'] = expense.cost_center_id.id
            account_move.append(move_line)

            # Calculate tax lines and adjust base line
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            account_move[-1]['price'] = taxes['total_excluded']
            account_move[-1]['tax_ids'] = [(6, 0, expense.tax_ids.ids)]
            account_move[-1]['payment_id'] = payment_id
            account_move[-1]['cost_center_id'] = self.sheet_id.cost_center_id.id
            account_move[-1]['analytic_account_id'] = self.sheet_id.analytic_account_id.id
            for tax in taxes['taxes']:
                account_move.append({
                    'type': 'tax',
                    'name': tax['name'],
                    'price_unit': tax['amount'],
                    'quantity': 1,
                    'price': tax['amount'],
                    'account_id': tax['account_id'] or move_line['account_id'],
                    'tax_line_id': tax['id'],
                    'expense_id': expense.id,
                    'payment_id': payment_id,
                    'cost_center_id': self.sheet_id.cost_center_id.id,
                    'analytic_account_id': self.sheet_id.analytic_account_id.id,
                })
        return account_move

    @api.multi
    def action_move_create(self):
        move_group_by_sheet = {}
        payment_id = False
        exp_total = exp_total_currency = 0
        move_lines = []
        for expense in self:
            # create the move that will contain the accounting entries
            if expense.sheet_id.id not in move_group_by_sheet:
                move = self.env['account.move'].create(expense._prepare_move_values())
                move_group_by_sheet[expense.sheet_id.id] = move
                payment_id = expense.sheet_id._create_payment()
            else:
                move = move_group_by_sheet[expense.sheet_id.id]
            company_currency = expense.company_id.currency_id
            diff_currency_p = expense.currency_id != company_currency
            #one account.move.line per expense (+taxes..)
            move_line = expense._pay_move_line_get(payment_id)
            # #create one more move line, a counterline for the total on payable account
            total, total_currency, move_line = expense._compute_expense_totals(company_currency, move_line, move.date)
            exp_total += total
            exp_total_currency += total_currency
            [(move_lines.append([move])) for move in move_line]
        if exp_total:
            settle_amount = exp_total
            variance_amount = 0
            if self[0].sheet_id.payment_mode == 'company_account':
                if not self[0].sheet_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (self[0].sheet_id.bank_journal_id.name))
                emp_account = self[0].sheet_id.bank_journal_id.default_credit_account_id.id
            else:
                # if not self[0].employee_id.address_home_id:
                #     raise UserError(_("No Home Address found for the employee %s, please configure one.") % (self[0].employee_id.name))
                advance_amount = 0
                if self[0].sheet_id.advance_id:
                    emp_account = self[0].sheet_id.partner_id.property_account_receivable_id.id
                    advance_amount = self[0].sheet_id.advance_id.paid_amount
                    variance_amount = advance_amount + exp_total
                    settle_amount = variance_amount < 0 and -advance_amount or exp_total
                else:
                    emp_account = self[0].sheet_id.partner_id.property_account_payable_id.id
            aml_name = "%s: %s" % (self[0].sheet_id.name, self[0].sheet_id.communication)
            move_lines.append([{
                'type': 'dest',
                'name': aml_name,
                'price': settle_amount,
                'account_id': emp_account,
                'date_maturity': move.date,
                'amount_currency': diff_currency_p and exp_total_currency or False,
                'currency_id': diff_currency_p and self[0].currency_id.id or False,
                'payment_id': payment_id,
                'cost_center_id': self[0].sheet_id.cost_center_id.id,
                'analytic_account_id': self[0].sheet_id.analytic_account_id.id,
            }])
            ap_emp_account = ""
            if variance_amount < 0:
                # ap_emp_account = self[0].sheet_id.bank_journal_id.default_credit_account_id.id
                # ap_emp_name = "Return " + self[0].sheet_id.advance_id.name
            # elif variance_amount < 0:
                ap_emp_account = self[0].sheet_id.partner_id.property_account_payable_id.id
                ap_emp_name = aml_name
            if ap_emp_account:
                move_lines.append([{
                    'type': 'dest',
                    'name': ap_emp_name,
                    'price': variance_amount,
                    'account_id': ap_emp_account,
                    'date_maturity': move.date,
                    'amount_currency': diff_currency_p and exp_total_currency or False,
                    'currency_id': diff_currency_p and self[0].currency_id.id or False,
                    'payment_id': payment_id,
                    'cost_center_id': self[0].sheet_id.cost_center_id.id,
                    'analytic_account_id': self[0].sheet_id.analytic_account_id.id,
                }])
            # convert eml into an osv-valid format
            lines = [(0, 0, expense._prepare_expense_move_line(x)) for [x] in move_lines]
            move.with_context(dont_create_taxes=True).write({'line_ids': lines})
            if expense.payment_mode == 'company_account':
                expense.sheet_id.write({'move_id': move.id})
                expense.sheet_id.paid_expense_sheets()
            else:
                expense.sheet_id.write({'account_move_id': move.id})
            for move in move_group_by_sheet.values():
                move.post()
        return True

    def _prepare_expense_move_line(self, line):
        '''
        This function prepares move line of account.move related to an expense
        '''
        # partner_id = self.employee_id.address_home_id.commercial_partner_id.id
        partner_id = self.sheet_id.partner_id.id
        return {
            'date_maturity': line.get('date_maturity'),
            'partner_id': partner_id,
            'name': line['name'][:64],
            'debit': line['price'] > 0 and line['price'],
            'credit': line['price'] < 0 and - line['price'],
            'account_id': line['account_id'],
            'analytic_line_ids': line.get('analytic_line_ids'),
            'amount_currency': line['price'] > 0 and abs(line.get('amount_currency')) or - abs(line.get('amount_currency')),
            'currency_id': line.get('currency_id'),
            'tax_line_id': line.get('tax_line_id'),
            'tax_ids': line.get('tax_ids'),
            'quantity': line.get('quantity', 1.00),
            'product_id': line.get('product_id'),
            'product_uom_id': line.get('uom_id'),
            'cost_center_id': line.get('cost_center_id'),
            'analytic_account_id': line.get('analytic_account_id'),
            'payment_id': line.get('payment_id'),
            'expense_id': line.get('expense_id'),
        }


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    @api.model
    def _default_partner(self):
        partner_id = self.env['ir.config_parameter'].sudo().get_param('default_expense_partner_id')
        # account_id = self.employee_id.address_home_id.property_account_receivable_id.id
        return self.env['res.partner'].browse(int(partner_id))

    name = fields.Char(
        string='Number',
        default='New',
        readonly=True,
    )
    job_id = fields.Many2one('hr.job', string='Job Title', readonly=True, states={'draft': [('readonly', False)]})
    report_date = fields.Date(string='Reported Date', default=fields.Date.today(), states={'draft': [('readonly', False)]})
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Reported User', readonly=True)
    cost_center_id = fields.Many2one('cost.center', required=True, string="Cost Center", ondelete="set null")
    analytic_account_id = fields.Many2one('account.analytic.account', required=True, string='Analytic Account', ondelete="set null")
    account_move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, ondelete='set null', copy=False)
    advance_id = fields.Many2one('hr.advance', string='Cash Advance', copy=False)
    advance_date = fields.Date(string='Paid Date', related='advance_id.account_validate_date', readonly=True)
    advance_amount = fields.Float(string='Advance Amount', related='advance_id.paid_amount', readonly=True, digits=dp.get_precision('Account'))
    total_amount = fields.Float(string='Settle Amount', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
    expense_amount = fields.Float(string='Expense Amount', digits=dp.get_precision('Account'), compute='_compute_amount')
    payment_id = fields.Many2one('account.payment', string='Payment', readonly=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='set null', copy=False)
    accounting_date = fields.Date(string="Payment Date")
    payment_mode = fields.Selection([("own_account", "Employee"), ("company_account", "Company")], related='', default='own_account', string="Payment By")
    partner_id = fields.Many2one('res.partner', string='Employee Partner', readonly=True, store=True, default=_default_partner, required=True)
    communication = fields.Char(string='Memo', required=True)
    journal_id = fields.Many2one('account.journal', string='Expense Journal', readonly=True,
                                 states={'done': [('readonly', True)], 'post': [('readonly', True)]},
                                 default=lambda self: self.env['res.config.settings'].get_values()['eam_journal_id'],
                                 help="The journal used when the expense is done.")
    advance_journal_id = fields.Many2one('account.journal', string='Advance Journal', readonly=True, store=True)
    ret_journal_id = fields.Many2one('account.journal', string='Transfer From Journal', readonly=True, store=True)
    order_id = fields.Many2one('sale.order', string="Sale Order", readonly=True, states={'submit': [('readonly', False)]}, ondelete="set null")
    request_id = fields.Many2one('sprogroup.purchase.request', string="Purchase Request", readonly=True, states={'submit': [('readonly', False)]}, ondelete="set null")
    department_id_charge_to = fields.Many2one('hr.department', string="Charge Department", readonly=True, states={'submit': [('readonly', False)]}, ondelete="restrict")
    created_sign_by = fields.Many2one('hr.employee', string='Dibuat', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_created_sign_by'))
    checked_sign_by = fields.Many2one('hr.employee', string='Diperiksa', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_checked_sign_by'))
    known_sign_by = fields.Many2one('hr.employee', string='Mengetahui', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_known_sign_by'))
    done_sign_by = fields.Many2one('hr.employee', string='Dilaksanakan', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_done_sign_by'))
    management_sign_by = fields.Many2one('hr.employee', string='Pengurus', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_management_sign_by'))
    # state = fields.Selection([('submit', 'Submitted'),
    #                           ('approve', 'Approved'),
    #                           ('post', 'Posted'),
    #                           ('done', 'Paid'),
    #                           ('cancel', 'Refused')
    #                           ], string='Status', index=True, readonly=True, track_visibility='none', copy=False, default='submit', required=True,
    # help='Expense Report State')

    @api.onchange('order_id')
    def _onchange_order_id(self):
        if self.order_id.id:
            self.cost_center_id = self.order_id.cost_center_id.id
            self.analytic_account_id = self.order_id.analytic_account_id.id
        else:
            self.cost_center_id = self.employee_id.cost_center_id.id
            self.analytic_account_id = self.employee_id.analytic_account_id.id

    @api.onchange('request_id')
    def _onchange_request_id(self):
        if self.request_id.id:
            self.cost_center_id = self.request_id.cost_center_id.id
            self.analytic_account_id = self.request_id.analytic_account_id.id
            self.order_id = self.request_id.salesorder_id.id
        else:
            self.cost_center_id = self.employee_id.cost_center_id.id
            self.analytic_account_id = self.employee_id.analytic_account_id.id
            self.order_id = False

    @api.onchange('department_id_charge_to')
    def _onchange_department_id_charge_to(self):
        if self.department_id_charge_to.id:
            self.cost_center_id = self.department_id_charge_to.cost_center_id.id
            self.analytic_account_id = self.department_id_charge_to.analytic_account_id.id
        else:
            self.cost_center_id = self.employee_id.cost_center_id.id
            self.analytic_account_id = self.employee_id.analytic_account_id.id

    @api.multi
    def approve_expense_sheets(self):
        # if not self.user_has_groups('hr_expense.group_hr_expense_user'):
        #     raise UserError(_("Only HR Officers can approve expenses"))
        # if not self.expense_line_ids or not self.expense_amount:
        #     raise UserError("Entry expense line, or expense amount cann't be zero!")
        self.write({'state': 'approve', 'responsible_id': self.env.user.id})

    @api.one
    @api.depends('expense_line_ids', 'expense_line_ids.total_amount', 'expense_line_ids.currency_id')
    def _compute_amount(self):
        total_amount = 0.0
        for expense in self.expense_line_ids:
            total_amount += expense.currency_id.with_context(
                date=expense.date,
                company_id=expense.company_id.id
            ).compute(expense.total_amount, self.currency_id)
        self.expense_amount = total_amount
        if self.advance_amount:
            self.total_amount = self.expense_amount - self.advance_amount
        else:
            self.total_amount = self.expense_amount

    @api.onchange('payment_mode')
    def _on_change_payment_mode(self):
        for expense in self.expense_line_ids:
            expense.payment_mode = self.payment_mode

    @api.multi
    def register_payment(self, payment_line, writeoff_acc_id=False, writeoff_journal_id=False):
        """ Reconcile payable/receivable lines from the invoice with payment_line """
        line_to_reconcile = self.env['account.move.line']
        for exp in self:
            line_to_reconcile += exp._get_aml_for_register_payment()
        return (line_to_reconcile + payment_line).reconcile(writeoff_acc_id, writeoff_journal_id)

    @api.multi
    def _get_aml_for_register_payment(self):
        """ Get the aml to consider to reconcile in register payment """
        self.ensure_one()
        return self.account_move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))

    @api.multi
    def _get_aml_for_register_advance(self):
        """ Get the aml to consider to reconcile in register payment """
        self.ensure_one()
        return self.account_move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('receivable'))

    def _get_payment_val(self, auto_settle_pay_emp):
        journal = self.bank_journal_id
        payment_methods = (self.total_amount < 0) and journal.outbound_payment_method_ids or journal.inbound_payment_method_ids
        val = {
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'payment_type': -self.total_amount < 0 and 'outbound' or 'inbound',
            # 'partner_id': self.employee_id.address_home_id.commercial_partner_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': 'supplier',
            'journal_id': journal.id,
            'payment_date': self.accounting_date,
            'currency_id': self.currency_id.id,  # diff_currency_p and self.currency_id.id or journal_currency.id,
            'amount': self.total_amount,  # diff_currency_p and abs(total_currency) or abs(total),
            'name': self.name,
            'company_id': self.company_id.id,
            'communication': self.name
        }
        if not auto_settle_pay_emp:
            val.update({'state': 'reconciled',})
        return val

    def _get_transfer_val(self, auto_settle_pay_emp):
        journal = self.bank_journal_id
        payment_methods = (self.total_amount < 0) and journal.outbound_payment_method_ids or journal.inbound_payment_method_ids
        ret_journal_id = self.env['ir.config_parameter'].sudo().get_param('ret_journal_id')
        val = {
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'payment_type': 'transfer',
            'partner_id': False, # self.employee_id.address_home_id.commercial_partner_id.id,
            # 'partner_type': 'supplier',
            'journal_id': int(ret_journal_id),
            'destination_journal_id': journal.id,
            'payment_date': self.accounting_date,
            'currency_id': self.currency_id.id,  # diff_currency_p and self.currency_id.id or journal_currency.id,
            'amount': abs(self.total_amount),  # diff_currency_p and abs(total_currency) or abs(total),
            'name': self.name,
            'company_id': self.company_id.id,
            'communication': '%s Return %s' % (self.name, self.advance_id.name),
            # 'move_name': move.name,
            # 'state': 'posted',
        }
        if not auto_settle_pay_emp:
            val.update({'state': 'reconciled',})
        return val

    @api.multi
    def _get_adv_move_line(self):
        """ Get the aml to consider to reconcile in register payment """
        self.ensure_one()
        return self.advance_id.move_id.line_ids.filtered(
            lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))

    @api.multi
    def reconcile_advance(self, writeoff_acc_id=False, writeoff_journal_id=False):
        """ Reconcile cash advance to expenses """
        line_to_reconcile = self.env['account.move.line']
        for exp in self:
            line_to_reconcile += exp._get_aml_for_register_advance()
        adv_move_line = exp._get_adv_move_line()
        adv_move_line.payment_id.update({'state': 'reconciled'})
        return (line_to_reconcile + adv_move_line).reconcile(writeoff_acc_id, writeoff_journal_id)

    def _create_payment(self, auto_settle_pay_emp = False):
        payment_id = False
        if self.payment_mode == 'company_account' or auto_settle_pay_emp:
            if self.total_amount > 0:
                payment = self.env['account.payment'].create(self._get_payment_val(auto_settle_pay_emp))
                if auto_settle_pay_emp:
                    payment.sheet_ids = self.ids
                    payment.post_expense()
                    move = self.env['account.move'].search([('name', '=', payment.move_name)], limit=1)
                    for line in move.line_ids:
                        line.name = '%s: %s' % (self.name, self.communication)
                payment_id = payment.id
            else:
                payment = self.env['account.payment'].create(self._get_transfer_val(auto_settle_pay_emp))
                if auto_settle_pay_emp:
                    payment.sheet_ids = self.ids
                    payment.post_expense()
                    move_lines = self.env['account.move.line'].search([('payment_id', '=', payment.id)])
                    for line in move_lines:
                        line.name = '%s: %s' % (self.name, self.communication)
                payment_id = payment.id
            self.write({'payment_id': payment_id, 'state': 'done'})
        return payment_id

    @api.multi
    def set_to_paid(self, payment_id = False):
        if payment_id:
            self.write({'payment_id': payment_id, 'state': 'done'})

    @api.multi
    def action_sheet_move_create(self):
        # res = super(HrExpenseSheet, self).action_sheet_move_create()
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        # if self.payment_mode == 'own_account' and expense_line_ids:
        #     self.write({'state': 'post'})
        # else:
        self.write({'state': 'done'})

        # create payment or return cash advance
        if self.payment_mode == 'own_account' and self.total_amount < 0:
            payment_id = self._create_payment(True)

        if self.advance_id:
            self.reconcile_advance()
            self.advance_id.update({'state': 'done'})

        if self.payment_mode == 'own_account' and self.total_amount > 0:
            payment_id = self._create_payment(True)

        return res

    def _populate_advance_lines(self):
        lines = []
        for line in self.advance_id.advance_line_ids:
            value = {
                'product_id': line.product_id.id,
                'name': line.description,
                'date': self.report_date,
                'employee_id': self.employee_id.id,
                'quantity': line.quantity,
                'product_uom_id': line.product_uom_id.id,
                'currency_id': self.currency_id.id,
                'unit_amount': line.unit_amount,
                'payment_mode': self.payment_mode,
                'advance_amount': line.total_amount,
                'advance_currency_id': line.currency_id.id,
                'advance_expense_id': line.id,
            }
            lines.append(value)
        return lines

    @api.onchange('advance_id')
    def _onchange_product_id(self):
        self.advance_journal_id = False
        self.ret_journal_id = False
        self.expense_line_ids = False
        self.order_id = False
        self.request_id = False
        self.department_id_charge_to = False
        self.cost_center_id = self.employee_id.cost_center_id.id
        self.analytic_account_id = self.employee_id.analytic_account_id.id
        if self.advance_id:
            self.expense_line_ids = [[0, False, line] for line in self._populate_advance_lines()]
            self.payment_mode = 'own_account'
            self.advance_journal_id = self.advance_id.journal_id.id
            ret_journal_id = self.env['ir.config_parameter'].sudo().get_param('ret_journal_id')
            self.ret_journal_id = int(ret_journal_id)
            self.order_id = self.advance_id.order_id.id
            self.request_id = self.advance_id.request_id.id
            self.department_id_charge_to = self.advance_id.department_id_charge_to.id
            self.cost_center_id = self.advance_id.cost_center_id.id
            self.analytic_account_id = self.advance_id.analytic_account_id.id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        super(HrExpenseSheet, self)._onchange_employee_id()
        self.cost_center_id = self.employee_id.cost_center_id.id
        self.analytic_account_id = self.employee_id.analytic_account_id.id
        self.job_id = self.employee_id.job_id.id
        # self.partner_id = self.employee_id.address_home_id and self.employee_id.address_home_id.id or False
        for sheet in self:
            for line in sheet.expense_line_ids:
                line.employee_id = sheet.employee_id

    @api.multi
    def cancel(self):
        # If has advance, unreconcile it first
        if self.advance_id:
            self.advance_id.move_id.remove_reconcile()
            self.advance_id.payment_id.update({'state': 'posted'})

        if self.move_id:
            self.move_id.remove_reconcile()
            self.move_id.button_cancel()
            self.move_id.unlink()
        if self.account_move_id:
            self.account_move_id.remove_reconcile()
            self.account_move_id.button_cancel()
            self.account_move_id.unlink()
        if self.payment_id:
            self.payment_id.update({'move_name': False})
            self.payment_id.cancel()
            self.payment_id.unlink()
        if self.advance_id:
            self.advance_id.update({'state': 'paid'})
        self.state = 'cancel'

    @api.multi
    def check_consistency(self):
        for rec in self:
            expense_lines = rec.expense_line_ids
            if not expense_lines:
                continue
            if any(expense.employee_id != rec.employee_id for expense in expense_lines):
                raise UserError(_("Expenses must belong to the same Employee."))
            if any(expense.payment_mode != expense_lines[0].payment_mode for expense in expense_lines):
                raise UserError(_("Expenses must have been paid by the same entity (Company or employee)"))

    @api.model
    def create(self, vals):
        vals.update({'name': self.env['ir.sequence'].next_by_code('hr.expense.sheet')})
        sheet = super(HrExpenseSheet, self).create(vals)
        self._update_advance_info()
        return sheet

    @api.multi
    def write(self, vals):
        res = super(HrExpenseSheet, self).write(vals)
        self._update_advance_info()
        return res

    def _update_advance_info(self):
        for expense in self:
            advance = self.env['hr.advance'].search([('expense_id', '=', expense.id)])
            if advance and advance.id != expense.advance_id:
                advance.update({'expense_id': False})
            if expense.advance_id:
                self.env['hr.advance'].search([('id', '=', expense.advance_id.id)]).update({'expense_id': expense.id})
