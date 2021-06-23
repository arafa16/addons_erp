# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from werkzeug import url_encode

class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
    _name = "hr.expense.payment.wizard"
    _description = "Expense Register Payment Wizard"

    @api.model
    def _default_partner_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)
        # return expense_sheet.address_id.id or expense_sheet.employee_id.id and expense_sheet.employee_id.address_home_id.id
        return expense_sheet.employee_id.id and expense_sheet.employee_id.address_home_id.id

    sheet_id = fields.Many2one('hr.expense.sheet', string='Expense No.', readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, readonly=True, default=_default_partner_id)
    ret_journal_id = fields.Many2one('account.journal', string='Transfer From Journal', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Payment Method', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type', required=True)
    amount = fields.Monetary(string='Payment Amount', required=True)
    advance_amount = fields.Monetary(string='Advance Amount')
    expense_amount = fields.Monetary(string='Expense Amount')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    communication = fields.Char(string='Description')
    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    payment_mode = fields.Selection([("own_account", "Employee (to reimburse)"), ("company_account", "Company")], string="Payment By")

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0 and self.advance_amount == 0:
            raise ValidationError(_('The payment amount must be strictly positive.'))

    @api.one
    @api.depends('journal_id')
    def _compute_hide_payment_method(self):
        if not self.journal_id:
            self.hide_payment_method = True
            return
        journal_payment_methods = self.journal_id.outbound_payment_method_ids
        self.hide_payment_method = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            return {'domain': {'payment_method_id': [('payment_type', '=', 'outbound'), ('id', 'in', payment_methods.ids)]}}
        return {}

    @api.multi
    def expense_post_payment(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)

        expense_sheet.update({
            # 'partner_id': self.partner_id.id,
            'bank_journal_id': self.journal_id.id,
            # 'total_amount': self.amount,
            'accounting_date': self.payment_date,
            # 'payment_mode': self.payment_mode,
            # 'communication': self.communication,
        })
        expense_sheet.action_sheet_move_create()
        return {'type': 'ir.actions.act_window_close'}
