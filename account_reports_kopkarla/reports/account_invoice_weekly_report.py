# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api
import datetime

class AccountInvoiceWeeklyReport(models.Model):
    _name = "account.invoice.weekly.report"
    _description = "Weekly Invoices Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    @api.multi
    @api.depends('currency_id', 'date', 'price_total', 'residual')
    def _compute_amounts_in_user_currency(self):
        """Compute the amounts in the currency of the user
        """
        context = dict(self._context or {})
        user_currency_id = self.env.user.company_id.currency_id
        currency_rate_id = self.env['res.currency.rate'].search([
            ('rate', '=', 1),
            '|', ('company_id', '=', self.env.user.company_id.id), ('company_id', '=', False)], limit=1)
        base_currency_id = currency_rate_id.currency_id
        ctx = context.copy()
        for record in self:
            ctx['date'] = record.date
            record.user_currency_price_total = base_currency_id.with_context(ctx).compute(record.price_total, user_currency_id)
            record.user_currency_residual = base_currency_id.with_context(ctx).compute(record.residual, user_currency_id)

    date = fields.Date(readonly=True)
    week_of_month = fields.Selection([('1', 'Minggu 1'),('2', 'Minggu 2'),('3', 'Minggu 3'),
                                      ('4', 'Minggu 4'),('5', 'Minggu 5')], string='Week', readonly=True)
    # payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term', readonly=True)
    # fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position', readonly=True)
    # currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', string='Partner Company', help="Commercial Entity")
    # company_id = fields.Many2one('res.company', string='Company', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
    price_total = fields.Float(string='Total', readonly=True)
    residual = fields.Float(string='Outstanding', readonly=True)
    # user_currency_price_total = fields.Float(string="Total Without Tax", compute='_compute_amounts_in_user_currency', digits=0)
    # price_average = fields.Float(string='Average Price', readonly=True, group_operator="avg")
    # user_currency_price_average = fields.Float(string="Average Price", compute='_compute_amounts_in_user_currency', digits=0)
    # currency_rate = fields.Float(string='Currency Rate', readonly=True, group_operator="avg", groups="base.group_multi_currency")
    # nbr = fields.Integer(string='# of Lines', readonly=True)  # TDE FIXME master: rename into nbr_lines
    type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
        ], readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
        ], string='Invoice Status', readonly=True)
    date_due = fields.Date(string='Due Date', readonly=True)
    reference = fields.Char(readonly=True)
    # partner_bank_id = fields.Many2one('res.partner.bank', string='Bank Account', readonly=True)
    # user_currency_residual = fields.Float(string="Total Residual", compute='_compute_amounts_in_user_currency', digits=0)
    # country_id = fields.Many2one('res.country', string='Country of the Partner Company')

    # _depends = {
    #     'account.invoice': [
    #         'account_id', 'amount_total_company_signed', 'commercial_partner_id', 'company_id',
    #         'currency_id', 'date_due', 'date_invoice', 'fiscal_position_id',
    #         'journal_id', 'partner_bank_id', 'partner_id', 'payment_term_id',
    #         'residual', 'state', 'type', 'user_id',
    #     ],
    #     'account.invoice.line': [
    #         'account_id', 'invoice_id', 'price_subtotal', 'product_id',
    #         'quantity', 'uom_id', 'account_analytic_id',
    #     ],
    #     'product.product': ['product_tmpl_id'],
    #     'product.template': ['categ_id'],
    #     'product.uom': ['category_id', 'factor', 'name', 'uom_type'],
    #     'res.currency.rate': ['currency_id', 'name'],
    #     'res.partner': ['country_id'],
    # }

    # def _select(self):
    #     select_str = """
    #         SELECT sub.id, sub.date, to_char(sub.date, 'W') as week_of_month, sub.product_id, sub.partner_id, sub.country_id, sub.account_analytic_id,
    #             sub.payment_term_id, sub.uom_name, sub.currency_id, sub.journal_id,
    #             sub.fiscal_position_id, sub.user_id, sub.company_id, sub.nbr, sub.type, sub.state,
    #             sub.categ_id, sub.date_due, sub.account_id, sub.account_line_id, sub.partner_bank_id, sub.price_total as price_total,
    #             COALESCE(cr.rate, 1) as currency_rate, sub.residual as residual, sub.commercial_partner_id as commercial_partner_id
    #     """
    #     return select_str

    def _select(self):
        select_str = """
                SELECT ai.id AS id,
                    ai.date_invoice AS date, ai.reference,
                    to_char(ai.date_invoice, 'W') as week_of_month, 
                    ai.partner_id, ai.journal_id, ai.user_id,
                    ai.type, ai.state, ai.date_due,
                    ai.amount_total AS price_total, ai.residual AS residual,
                    ai.commercial_partner_id as commercial_partner_id
        """
        return select_str

    def _from(self):
        from_str = """
            FROM account_invoice ai
                JOIN res_partner partner ON ai.commercial_partner_id = partner.id
                JOIN res_partner partner_ai ON ai.partner_id = partner_ai.id
                JOIN (
                    -- Temporary table to decide if the qty should be added or retrieved (Invoice vs Credit Note)
                    SELECT id,(CASE
                         WHEN ai.type::text = ANY (ARRAY['in_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN -1
                            ELSE 1
                        END) AS sign,(CASE
                         WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN -1
                            ELSE 1
                        END) AS sign_qty
                    FROM account_invoice ai
                ) AS invoice_type ON invoice_type.id = ai.id
        """
        return from_str

    # def _where(self):
    #     where_str = """
    #         WHERE state in ('open', 'paid')
    #     """
    #     return where_str

    # def _group_by(self):
    #     group_by_str = """
    #             GROUP BY ai.id, ai.date_invoice,
    #                 ai.partner_id, ai.payment_term_id, u2.name, u2.id, ai.currency_id, ai.journal_id,
    #                 ai.fiscal_position_id, ai.user_id, ai.company_id, ai.type, ai.state, pt.categ_id,
    #                 ai.date_due, ai.account_id, ail.account_id, ai.partner_bank_id, ai.residual_company_signed,
    #                 ai.amount_total_company_signed, ai.commercial_partner_id, coalesce(partner.country_id, partner_ai.country_id)
    #     """
    #     return group_by_str

    @api.model_cr
    def init(self):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            WITH currency_rate AS (%s)
            %s
            %s
        )""" % (
                    self._table, self.env['res.currency']._select_companies_rates(),
                    self._select(), self._from()))
