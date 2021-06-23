from odoo import models, fields, api, _
from odoo.exceptions import Warning,UserError
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import *
from odoo import tools

class AccountMoveLineTax(models.Model):
    _name = "account.move.line.tax"
    _description = "Tax Journal Report"
    _auto = False

    name = fields.Char(string="Label")
    move_id = fields.Many2one('account.move', string='Journal Entry', ondelete="cascade",
                              help="The move of this entry line.", index=True, required=True, auto_join=True)
    date = fields.Date(related='move_id.date', string='Date', index=True, store=True, copy=False)  # related is required
    tax_line_id = fields.Many2one('account.tax', string='Originator tax', ondelete='restrict')
    journal_id = fields.Many2one('account.journal', related='move_id.journal_id', string='Journal',
        index=True, store=True, copy=False)  # related is required
    ref = fields.Char(related='move_id.ref', string='Reference', store=True, copy=False, index=True)
    invoice_id = fields.Many2one('account.invoice', oldname="invoice")
    payment_id = fields.Many2one('account.payment', string="Originator Payment", help="Payment that created this entry", copy=False)
    account_id = fields.Many2one('account.account', string='Account', required=True, index=True,
                                 ondelete="cascade", domain=[('deprecated', '=', False)],
                                 default=lambda self: self._context.get('account_id', False))
    user_type_id = fields.Many2one('account.account.type', related='account_id.user_type_id', index=True, store=True, oldname="user_type", readonly=True)
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", readonly=True,
        help='Utility field to express amount currency', store=True)
    tax_base_amount = fields.Monetary(string="Base Amount", compute='_compute_tax_base_amount', currency_field='company_currency_id', store=True)
    debit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    balance = fields.Monetary(compute='_store_balance', store=True, currency_field='company_currency_id',
        help="Technical field holding the debit - credit in order to open meaningful graph views from reports")
    tax_no = fields.Char("Tax Number", copy=False)
    tax_date = fields.Date('Tax Date', copy=False)

    @api.model_cr
    def init(self):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE OR REPLACE VIEW %s AS (
            select l.id, l.name, l.move_id, l.date, l.tax_line_id, l.journal_id, l.ref, l.invoice_id, l.payment_id,
                    l.account_id, l.user_type_id, l.company_currency_id, l.tax_base_amount, l.debit, l.credit, l.balance,
                    l.tax_no, l.tax_date
            from account_move_line l inner join account_move m on l.move_id = m.id
            where m.state = 'posted' and l.tax_line_id is not null
        )""" % self._table)