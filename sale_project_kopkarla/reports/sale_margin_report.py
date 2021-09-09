# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleMarginReport(models.Model):
    _name = "sale.margin.report"
    _description = "Sales Margin Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    name = fields.Char('Sales Order', readonly=True)
    date = fields.Datetime('Date Order', readonly=True)
    confirmation_date = fields.Datetime('Confirmation Date', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    amount_untaxed = fields.Float('Sales Total', readonly=True)
    # amount_tax = fields.Float('Tax Total', readonly=True)
    # amount_total = fields.Float('Total', readonly=True)
    purchase_amount = fields.Float('Purchase Total', readonly=True)
    margin_amount = fields.Float('Margin Total', readonly=True)
    nbr = fields.Integer('# of Sales', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', readonly=True)
    cost_center_id = fields.Many2one("cost.center", string="Cost Center", readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Channel', readonly=True, oldname='section_id')
    country_id = fields.Many2one('res.country', 'Partner Country', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Commercial Entity', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT s.id,
                    s.amount_untaxed,
                    s.purchase_amount,
                    (s.amount_untaxed - s.purchase_amount) as margin_amount,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order as date,
                    s.confirmation_date as confirmation_date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    s.pricelist_id as pricelist_id,
                    s.cost_center_id as cost_center_id,
                    s.analytic_account_id as analytic_account_id,
                    s.team_id as team_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
                    sale_order s
                        join res_partner partner on s.partner_id = partner.id
                        left join product_pricelist pp on (s.pricelist_id = pp.id)
                        left join currency_rate cr on (cr.currency_id = pp.currency_id and
                            cr.company_id = s.company_id and
                            cr.date_start <= coalesce(s.date_order, now()) and
                            (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY s.id,
                    s.name,
                    s.date_order,
                    s.confirmation_date,
                    s.partner_id,
                    s.user_id,
                    s.state,
                    s.company_id,
                    s.pricelist_id,
                    s.cost_center_id,
                    s.analytic_account_id,
                    s.team_id,
                    partner.country_id,
                    partner.commercial_partner_id
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

