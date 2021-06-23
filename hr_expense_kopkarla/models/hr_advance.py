# -*- coding: utf-8 -*-

import time
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import pytz

from odoo.exceptions import UserError, Warning
from odoo import models, fields, api, _
from odoo.tools import float_compare, float_is_zero

class HRAdvance(models.Model):
    _name = 'hr.advance'
    _description = "Employee Cash Advance"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'

    @api.model
    def get_currency(self):
        return self.env.user.company_id.currency_id
        
    @api.multi
    @api.depends('advance_line_ids', 'advance_line_ids.total_amount')
    def _compute_total_amount_expense(self):
        for rec in self:
            rec.total_amount_expense = 0.0
            for line in rec.advance_line_ids:
                rec.total_amount_expense += line.total_amount
            
    @api.multi
    @api.depends('journal_id', 'currency_id','comment')
    def _compute_paid_currency(self):
        for rec in self:
            if not rec.journal_id.currency_id:
                rec.paid_in_currency = rec.company_id.currency_id.id
            else:  
                rec.paid_in_currency = rec.journal_id.currency_id
    
    @api.multi
    @api.depends('move_id', 'move_id.amount')
    def _compute_payed_amount(self):
        for rec in self:
            rec.paid_amount = rec.move_id.amount

    @api.model
    def _default_advance_account(self):
        # account_id = self.env['ir.config_parameter'].sudo().get_param('hr_expense_kopkarla.advance_account_id')
        account_id = self.employee_id.address_home_id.property_account_receivable_id.id
        return self.env['account.account'].browse(int(account_id))

    @api.model
    def _default_partner(self):
        partner_id = self.env['ir.config_parameter'].sudo().get_param('default_expense_partner_id')
        # account_id = self.employee_id.address_home_id.property_account_receivable_id.id
        return self.env['res.partner'].browse(int(partner_id))

    name = fields.Char(string='Number', default='New') # ,readonly=True)
    employee_id = fields.Many2one('hr.employee', required=True, readonly=True, string="Employee",default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1), states={'draft': [('readonly', False)]})
    request_date = fields.Date(string='Requested Date', default=fields.Date.today(), readonly=True, states={'draft': [('readonly', False)]})
    plan_date = fields.Date(string='Plan Date', default=fields.Date.today(), readonly=True, states={'draft': [('readonly', False)]})
    confirm_date = fields.Date(string='Confirmed Date', readonly=True, copy=False)
    hr_validate_date = fields.Date(string='Approved Date', readonly=True, copy=False)
    account_validate_date = fields.Date(string='Paid Date', readonly=True, copy=False)
    accounting_date = fields.Date(string="Payment Date", copy=False, default=fields.Date.today())
    confirm_by_id = fields.Many2one('res.users', string='Confirmed By', readonly=True, copy=False)
    hr_manager_by_id = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    account_by_id = fields.Many2one('res.users', string='Paid By', readonly=True, copy=False)
    department_id = fields.Many2one('hr.department', string='Department', store=True, readonly=True, states={'draft': [('readonly', False)]})
    job_id = fields.Many2one('hr.job', string='Job Title', store=True, readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', default=get_currency, required=True, readonly=True, states={'draft': [('readonly', False)]})
    comment = fields.Text(string='Comment')
    total_amount_expense = fields.Float(string='Requested Amount', store=True, compute='_compute_total_amount_expense', digits=dp.get_precision('Account'))
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Requested User', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company', readonly=True)
    reason_for_advance = fields.Text(string='Reason For Advance', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    state = fields.Selection(selection=[
                        ('draft', 'Draft'), \
                        ('confirm', 'Confirmed'), \
                        ('approved_hr_manager', 'Approved'),\
                        ('paid', 'Paid'),\
                        ('done', 'Done'),\
                        ('cancel', 'Cancelled'),\
                        ('reject', 'Rejected')],string='State', \
                        default='draft', track_visibility='onchange') # , readonly=True)
    partner_id = fields.Many2one('res.partner', string='Employee Partner', store=True, default=_default_partner, required=True) # , readonly=True)
    journal_id = fields.Many2one('account.journal', string='Payment Method')
    payment_id = fields.Many2one('account.payment', string='Payment', readonly=True)
    paid_in_currency = fields.Many2one('res.currency', string='Paid in Currency',compute='_compute_paid_currency')
    account_id = fields.Many2one('account.account', string='Advance Account', required=False, store=True, default=_default_advance_account)
    
    move_id = fields.Many2one('account.move', string = 'Journal Entry', readonly=True)
    advance_line_ids = fields.One2many('hr.advance.line', 'advance_line_id', string='Advance Lines', copy=False)
    paid_amount = fields.Float(compute=_compute_payed_amount, string='Paid Amount', store=True, digits=dp.get_precision('Account'))
    is_paid = fields.Boolean(string='Is Paid')
    cost_center_id = fields.Many2one('cost.center', string="Cost Center", required=True, ondelete="set null")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=True, ondelete="set null")
    expense_id = fields.Many2one('hr.expense.sheet', string="Expense", readonly=True, ondelete="set null")
    order_id = fields.Many2one('sale.order', string="Sale Order", readonly=True, states={'draft': [('readonly', False)]}, ondelete="set null")
    request_id = fields.Many2one('sprogroup.purchase.request', string="Purchase Request", readonly=True, states={'draft': [('readonly', False)]}, ondelete="set null")
    department_id_charge_to = fields.Many2one('hr.department', string="Charge Department", readonly=True, states={'draft': [('readonly', False)]}, ondelete="restrict")
    aging_days = fields.Integer('Aging', compute='_get_aging_day')
    created_sign_by = fields.Many2one('hr.employee', string='Dibuat', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_created_sign_by'))
    checked_sign_by = fields.Many2one('hr.employee', string='Diperiksa', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_checked_sign_by'))
    known_sign_by = fields.Many2one('hr.employee', string='Mengetahui', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_known_sign_by'))
    done_sign_by = fields.Many2one('hr.employee', string='Dilaksanakan', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_done_sign_by'))
    management_sign_by = fields.Many2one('hr.employee', string='Pengurus', default=lambda self: self.env['res.config.settings'].get_values().get('default_exp_management_sign_by'))

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
        else:
            self.cost_center_id = self.employee_id.cost_center_id.id
            self.analytic_account_id = self.employee_id.analytic_account_id.id

    @api.onchange('department_id_charge_to')
    def _onchange_department_id_charge_to(self):
        if self.department_id_charge_to.id:
            self.cost_center_id = self.department_id_charge_to.cost_center_id.id
            self.analytic_account_id = self.department_id_charge_to.analytic_account_id.id
        else:
            self.cost_center_id = self.employee_id.cost_center_id.id
            self.analytic_account_id = self.employee_id.analytic_account_id.id

    @api.depends('account_validate_date')
    def _get_aging_day(self):
        for adv in self:
            if adv.state != 'paid':
                adv.aging_days = 0
            else:
                adv.aging_days = (pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone("Asia/Jakarta")).date() - datetime.strptime(adv.accounting_date, DF).date()).days

    @api.model
    def create(self, vals):
        default_payment_journal_id = self.env['ir.config_parameter'].sudo().get_param('default_payment_id')
        # vals.update({'name': self.env['ir.sequence'].next_by_code('hr.advance'),
        #              'journal_id': default_payment_journal_id})
        vals.update({'journal_id': default_payment_journal_id})
        return super(HRAdvance, self).create(vals)

    @api.onchange('employee_id') #, 'employee_id.address_home_id')
    def get_department(self):
        for line in self:
            line.department_id = line.employee_id.department_id.id
            line.cost_center_id = line.employee_id.cost_center_id.id
            line.analytic_account_id = line.employee_id.analytic_account_id.id
            line.job_id = line.employee_id.job_id.id
            line.manager_id = line.employee_id.parent_id.id
            # line.partner_id = line.employee_id.address_home_id and line.employee_id.address_home_id.id or False

    @api.onchange('department_id_charge_to')
    def get_charge_to(self):
        if self.department_id_charge_to.id:
            self.cost_center_id = self.department_id_charge_to.cost_center_id.id
            self.analytic_account_id = self.department_id_charge_to.analytic_account_id.id

    @api.multi
    def request_set(self):
        self.state = 'draft'
    
    @api.multi
    def exit_cancel(self):
        if self.move_id:
            self.move_id.button_cancel()
            self.move_id.unlink()
        if self.payment_id:
            self.payment_id.update({'move_name': False})
            self.payment_id.unlink()
        self.state = 'cancel'

    def validate_cash_advance(self):
        res = self.env['res.config.settings'].get_values()
        if not res.get('multi_cash_advance'):
            advance = self.env['hr.advance'].sudo().search([('employee_id', '=', self.employee_id.id), ('state', '=', 'paid')])
            if advance:
                raise UserError(_('Please settle cash advance number %s before request a new one.' % advance.name))

    @api.multi
    def get_confirm(self, vals):
        if not self.advance_line_ids:
           raise Warning(_('Please add some advance expense lines.'))
        else:
            self.validate_cash_advance()
            if self.name == 'New':
                self.name = self.env['ir.sequence'].next_by_code('hr.advance')
            self.state = 'confirm'
            self.confirm_date = time.strftime('%Y-%m-%d')
            self.confirm_by_id = self.env.user.id
   
    @api.multi
    def get_apprv_hr_manager(self):
        self.validate_cash_advance()
        self.state = 'approved_hr_manager'
        self.hr_validate_date = time.strftime('%Y-%m-%d')
        self.hr_manager_by_id = self.env.user.id

    @api.multi
    def set_paid(self, payment_id, move_id, payment_wizard = False):
        val = { 'move_id': move_id,
                'payment_id': payment_id,
                'move_check': True,
                'state': 'paid',
                'account_validate_date': time.strftime('%Y-%m-%d'),
                'account_by_id': self.env.user.id,
                'is_paid': True,}
        if payment_wizard:
            val['journal_id'] = payment_wizard.journal_id.id
            val['accounting_date'] = payment_wizard.payment_date
            val['paid_amount'] = payment_wizard.amount
        self.write(val)

    @api.multi
    def get_done(self):
        self.state = 'done'
    
    @api.multi
    def get_reject(self):
        self.state = 'reject'

    def _get_payment_val(self, move_name):
        journal = self.journal_id
        payment_methods = (self.paid_amount < 0) and journal.outbound_payment_method_ids or journal.inbound_payment_method_ids
        val = {
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'payment_type': -self.paid_amount < 0 and 'outbound' or 'inbound',
            'partner_id': self.partner_id.id,
            'partner_type': 'supplier',
            'journal_id': journal.id,
            'payment_date': self.accounting_date,
            'currency_id': self.currency_id.id,  # diff_currency_p and self.currency_id.id or journal_currency.id,
            'amount': self.paid_amount,  # diff_currency_p and abs(total_currency) or abs(total),
            'name': self.name,
            'move_name': move_name,
            'company_id': self.company_id.id,
            'state': 'reconciled',
        }
        return val

    def _create_payment(self, move_name):
        payment = self.env['account.payment'].create(self._get_payment_val(move_name))
        payment.advance_ids = self.ids
        payment_id = payment.id
        # self.write({'payment_id': payment_id, 'state': 'done'})
        return payment_id

    @api.multi
    def action_sheet_move_advance(self):
        created_moves = self.env['account.move']
        prec = self.env['decimal.precision'].precision_get('Account')
        if not self.journal_id:
                raise UserError(_("No Credit account found for the Journal, please configure one.") % (self.journal_id))
        if not self.journal_id:
                raise UserError(_("No Debit account found for the account, please configure one.") % (self.account_id))
        for line in self:
            adv_exp_date = line.accounting_date # fields.Date.context_today(self)
            company_currency = line.company_id.currency_id
            current_currency = line.currency_id
            amount = current_currency.compute(line.total_amount_expense, company_currency)
            ref = line.name
            move_vals = {
                'ref': line.name,
                'date': adv_exp_date or False,
                'journal_id': line.journal_id.id,
                'narration': line.reason_for_advance,
            }
            move = self.env['account.move'].create(move_vals)
            payment_id = self._create_payment(move.name)
            move_line_debit = {
                'name': ref,
                'account_id': line.journal_id.default_credit_account_id.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': line.journal_id.id,
                'partner_id': line.partner_id.id,
#                 'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * line.total_amount_expense or 0.0,
                'cost_center_id': self.cost_center_id.id,
                'analytic_account_id': self.analytic_account_id.id,
            }
            move_line_credit = {
                'name': ref,
                'account_id': line.account_id.id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': line.journal_id.id,
                'partner_id': line.partner_id.id,
#                 'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'purchase' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and line.total_amount_expense or 0.0,
                'cost_center_id': self.cost_center_id.id,
                'analytic_account_id': self.analytic_account_id.id,
            }
            move['line_ids'] = [(0, 0, move_line_debit), (0, 0, move_line_credit)],
            move.post()
            line.set_paid(payment_id, move.id)
            created_moves |= move

        # if post_move and created_moves:
        #     created_moves.filtered(lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).post()
        return [x.id for x in created_moves]
    
    @api.multi
    def show_journal(self):
        action = self.env.ref('account.action_move_line_form')
        res = action.read()[0]
        res['domain'] = str([('id','=',self.move_id.id)])
        return res

    @api.multi
    def unlink(self):
        for advance in self:
            if advance.state not in ['draft', 'cancel', 'reject']:
                raise UserError(_('You cannot delete a document that not in draft / cancel / reject state.'))
        super(HRAdvance, self).unlink()


class HRAdvanceLine(models.Model):
    _name = "hr.advance.line"
    _description = "Advance Line"

    @api.multi
    @api.depends('unit_amount', 'quantity')
    def _compute_total_line_expense(self):
        for rec in self:
            amount_line = rec.unit_amount * rec.quantity
            rec.total_amount = amount_line

    product_id = fields.Many2one('product.product', string='Expense', required=True, domain=[('can_be_expensed', '=', True)])
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True, readonly=True,
                                     states={'draft': [('readonly', False)], 'refused': [('readonly', False)]},
                                     default=lambda self: self.env['product.uom'].search([], limit=1, order='id'))
    unit_amount = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    quantity = fields.Float(required=True, digits=dp.get_precision('Product Unit of Measure'), default=1)
    description = fields.Char(string='Description', required=True)
    total_amount = fields.Float(string='Subtotal', compute='_compute_total_line_expense',
                                digits=dp.get_precision('Account'))
    currency_id = fields.Many2one('res.currency', string='Currency', related='advance_line_id.currency_id',
                                  readonly=True, store=True)
    expense_line_ids = fields.One2many('hr.expense', 'sheet_id', string='Expense Lines', copy=False)
    advance_line_id = fields.Many2one('hr.advance', string="Advance Report")
    employee_id = fields.Many2one('hr.employee', required=True, string="Employee",
                                  related='advance_line_id.employee_id')
    name = fields.Char(
        string='Number',
        related='advance_line_id.name',
        readonly=1,
    )
    state = fields.Selection(
        related='advance_line_id.state',
    )
    reambursment = fields.Boolean(
        string='Reimbursement',
        default=False,
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.description = rec.product_id.name
            if rec.advance_line_id.company_id.currency_id != rec.advance_line_id.currency_id:
                amount = rec.advance_line_id.company_id.currency_id.compute(rec.product_id.standard_price,
                                                                            rec.advance_line_id.currency_id)
                rec.unit_amount = amount
            else:
                rec.unit_amount = rec.product_id.standard_price
