# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleRevaReport(models.Model):
    _name = "sale.reva.report"
    _description = "Sales Reva Status"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    name = fields.Char('Sales Order', readonly=True)
    date = fields.Date('Date Order', readonly=True)
    confirmation_date = fields.Date('Confirmation Date', readonly=True)
    delivery_date = fields.Date('Delivery Date', readonly=True)
    bast_date = fields.Date('BAST Date', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    # amount_untaxed = fields.Float('Sales Total', readonly=True)
    # amount_tax = fields.Float('Tax Total', readonly=True)
    # amount_total = fields.Float('Total', readonly=True)
    # purchase_amount = fields.Float('Purchase Total', readonly=True)
    # advance_amount = fields.Float('Advance Total', readonly=True)
    # expense_amount = fields.Float('Expense Total', readonly=True)
    price_total = fields.Float('Amount Total', readonly=True)
    price_subtotal = fields.Float('Untaxed Total', readonly=True)
    amt_to_invoice = fields.Float('Amount To Invoice', readonly=True)
    dpp_to_invoice = fields.Float('DPP To Invoice', readonly=True)
    draft_contract_to_invoice = fields.Float('Draft To Invoice', readonly=True)
    amt_invoiced = fields.Float('Amount Invoiced', readonly=True)
    dpp_invoiced = fields.Float('DPP Invoiced', readonly=True)
    amt_cancel = fields.Float('Amount Canceled', readonly=True)
    # sales_total = fields.Float('Sales Amount', readonly=True)
    nbr = fields.Integer('# of Sales', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', readonly=True)
    cost_center_id = fields.Many2one("cost.center", string="Cost Center", readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    # team_id = fields.Many2one('crm.team', 'Sales Channel', readonly=True, oldname='section_id')
    country_id = fields.Many2one('res.country', 'Partner Country', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Commercial Entity', readonly=True)
    state = fields.Selection([
        ('cancel', 'Cancelled'),
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('spvcheck', 'SPV Check'),
        ('assmancheck', 'Assman Check'),
        ('requestloa', 'Request LoA'),
        ('loaconfirmed', 'LoA Confirmed'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ], string='Status', readonly=True)
    jenis_so = fields.Selection([("common", "General Order"), ("Project", "Project"), ("datacom", "Trading Datacom"),
                                 ("rental", "Rental Order")], string='Order Type', readonly=True)
    reva_status = fields.Char(string='Reva Status', readonly=True)
    reva_group_id = fields.Many2one('enhanced.reva.group.tabel', 'Reva Group', readonly=True)
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term', readonly=True)
    est_invoice_date = fields.Date('Estimasi Invoice Date')

    spk_sementara = fields.Char('SPK User')
    nomor_spk = fields.Char('No. PO')
    tgl_spk = fields.Char('Tanggal PO')
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True)
    reva_notes = fields.Char('Catatan Proses Reva')
    nojar = fields.Char('Nomor Jaringan')
    proj_type = fields.Many2one('enhanced.sales.project.tabel', 'Jenis Project')
    ord_type = fields.Many2one('enhanced.sales.jenis.tabel', 'Jenis Order')
    pek_type = fields.Many2one('enhanced.sales.pekerjaan.tabel', 'Jenis Pekerjaan')

    requested_date = fields.Date('Requested Date', readonly=True)
    bast_no = fields.Char('DO / BAST Number', readonly=True)
    client_order_ref = fields.Char('Customer Reference', readonly=True)

    daily_tgl_mulai = fields.Date(string='TANGGAL MULAI')
    daily_tgl_selesai = fields.Date(string='TGL SELESAI')

    status_stage = fields.Char(string='Stage')
    status_pelaksanaan = fields.Selection(
        selection=[
            ('A', 'Not Started'),
            ('B', 'On Progress'),
            ('C', 'Stop Clock'),
            ('D', 'Done'),
            ('E', 'Cancel')
        ],
        string='Status Pelaksanaan')

    def _select(self):
        select_str = """
             SELECT s.id,
                    s.jenis_so,
                    rg.id as reva_group_id,
                    CONCAT(s.type_reva, ' ', r.name) AS reva_status,
                    -- s.amount_untaxed,
                    -- s.purchase_amount,
                    -- s.advance_amount,
                    -- s.expense_amount,
                    -- (s.amount_untaxed - s.purchase_amount - s.advance_amount - s.expense_amount) as total_amount,
                    sum(l.price_total / COALESCE(NULLIF(cr.rate, 0), 1.0)) as price_total,
                    sum(l.price_subtotal / COALESCE(NULLIF(cr.rate, 0), 1.0)) as price_subtotal, -- untaxed
                    -- sum(l.amt_to_invoice / COALESCE(NULLIF(cr.rate, 0), 1.0)) as amt_to_invoice,
                    case when sum(l.amt_to_invoice / COALESCE(NULLIF(cr.rate, 0), 1.0)) = 0 then 0
                         else sum(l.price_total / COALESCE(NULLIF(cr.rate, 0), 1.0)) - sum(l.amt_invoiced / COALESCE(NULLIF(cr.rate, 0), 1.0)) end as amt_to_invoice,
                    -- case when sum(l.amt_to_invoice / COALESCE(NULLIF(cr.rate, 0), 1.0)) = 0 then 0 
                    --      else sum((l.qty_to_invoice * l.price_unit) / COALESCE(NULLIF(cr.rate, 0), 1.0)) end as dpp_to_invoice,
                    case when sum(l.amt_to_invoice / COALESCE(NULLIF(cr.rate, 0), 1.0)) = 0 then 0 
                         else sum(l.price_subtotal / COALESCE(NULLIF(cr.rate, 0), 1.0)) - sum((l.qty_invoiced * l.price_unit) / COALESCE(NULLIF(cr.rate, 0), 1.0)) end as dpp_to_invoice,
                    0 as draft_contract_to_invoice,
                    sum(l.amt_invoiced / COALESCE(NULLIF(cr.rate, 0), 1.0)) as amt_invoiced,
                    -- case when sum(l.amt_invoiced / COALESCE(NULLIF(cr.rate, 0), 1.0)) = 0 then 0 
                    --     else sum((l.qty_invoiced * l.price_unit) / COALESCE(NULLIF(cr.rate, 0), 1.0)) end as dpp_invoiced,
                    sum((l.qty_invoiced * l.price_unit) / COALESCE(NULLIF(cr.rate, 0), 1.0)) as dpp_invoiced,
                    0 as amt_cancel,
                    -- s.amount_total as sales_total,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order::date as date,
                    s.confirmation_date::date as confirmation_date,
                    s.bast_date as bast_date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    s.pricelist_id as pricelist_id,
                    s.cost_center_id as cost_center_id,
                    s.analytic_account_id as analytic_account_id,
                    s.est_invoice_date,
                    s.delivery_doc as delivery_date,
                    s.payment_term_id as payment_term_id,
                    s.spk_sementara as spk_sementara,
                    s.nomor_spk as nomor_spk,
                    s.tgl_spk as tgl_spk,
                    s.partner_shipping_id as partner_shipping_id,
                    s.reva_notes as reva_notes,
                    s.nojar as nojar,
                    s.proj_type as proj_type,
                    s.ord_type as ord_type,
                    s.pek_type as pek_type,
                    -- s.team_id as team_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    s.requested_date::date as requested_date,
                    s.bast_no,
                    s.client_order_ref,
                    pt.create_date::date as daily_tgl_mulai,
                    pt.daily_tgl_selesai,
                    s.status_stage,
                    s.status_pelaksanaan
        """
        return select_str

    def _select_rental(self):
        select_str = """
             SELECT s.id,
                    s.jenis_so,
                    rg.id as reva_group_id,
                    CONCAT(s.type_reva, ' ', r.name) AS reva_status,
                    avg(s.amount_total) as price_total,
                    avg(s.amount_untaxed) as price_subtotal,
                    sum(ai1.amount_total) as amt_to_invoice,
                    avg(s.amount_untaxed) - sum(ai2.amount_untaxed) as dpp_to_invoice,
                    sum(ai1.amount_untaxed) as draft_contract_to_invoice,
                    sum(ai2.amount_total) as amt_invoiced,
                    sum(ai2.amount_untaxed) as dpp_invoiced,
                    0 as amt_cancel,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order::date as date,
                    s.confirmation_date::date as confirmation_date,
                    s.bast_date as bast_date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    s.pricelist_id as pricelist_id,
                    s.cost_center_id as cost_center_id,
                    s.analytic_account_id as analytic_account_id,
                    s.est_invoice_date,
                    s.delivery_doc as delivery_date,
                    s.payment_term_id as payment_term_id,
                    s.spk_sementara as spk_sementara,
                    s.nomor_spk as nomor_spk,
                    s.tgl_spk as tgl_spk,
                    s.partner_shipping_id as partner_shipping_id,
                    s.reva_notes as reva_notes,
                    s.nojar as nojar,
                    s.proj_type as proj_type,
                    s.ord_type as ord_type,
                    s.pek_type as pek_type,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    s.requested_date::date as requested_date,
                    s.bast_no,
                    s.client_order_ref,
                    pt.create_date::date as daily_tgl_mulai,
                    pt.daily_tgl_selesai,
                    s.status_stage,
                    s.status_pelaksanaan
        """
        return select_str

    def _select_cancel(self):
        select_str = """
             SELECT s.id,
                    s.jenis_so,
                    rg.id as reva_group_id,
                    CONCAT(s.type_reva, ' ', r.name) AS reva_status,
                    0 as price_total,
                    0 as price_subtotal,
                    0 as amt_to_invoice,
                    0 as dpp_to_invoice,
                    0 as draft_contract_to_invoice,
                    0 as amt_invoiced,
                    0 as dpp_invoiced,
                    sum(l.price_total / COALESCE(NULLIF(cr.rate, 0), 1.0)) as amt_cancel,
                    -- 0 as sales_total,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order::date as date,
                    s.confirmation_date::date as confirmation_date,
                    s.bast_date as bast_date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    s.pricelist_id as pricelist_id,
                    s.cost_center_id as cost_center_id,
                    s.analytic_account_id as analytic_account_id,
                    s.est_invoice_date,
                    s.delivery_doc as delivery_date,
                    s.payment_term_id as payment_term_id,
                    s.spk_sementara as spk_sementara,
                    s.nomor_spk as nomor_spk,
                    s.tgl_spk as tgl_spk,
                    s.partner_shipping_id as partner_shipping_id,
                    s.reva_notes as reva_notes,
                    s.nojar as nojar,
                    s.proj_type as proj_type,
                    s.ord_type as ord_type,
                    s.pek_type as pek_type,
                    -- s.team_id as team_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    s.requested_date::date as requested_date,
                    s.bast_no,
                    s.client_order_ref,
                    pt.create_date::date as daily_tgl_mulai,
                    pt.daily_tgl_selesai,
                    s.status_stage,
                    s.status_pelaksanaan
        """
        return select_str

    def _from(self):
        from_str = """
                sale_order_line l
                join sale_order s on (l.order_id=s.id)        
                join res_partner partner on s.partner_id = partner.id
                left join product_pricelist pp on (s.pricelist_id = pp.id)
                left join currency_rate cr on (cr.currency_id = pp.currency_id and
                    cr.company_id = s.company_id and
                    cr.date_start <= coalesce(s.date_order, now()) and
                    (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
                left join enhanced_reva_tabel r on s.stat_reva = r.id
                left join enhanced_reva_group_tabel rg on r.reva_id = rg.id
                left join project_task pt on s.id = pt.sale_order_id
        """
        return from_str

    def _from_rental(self):
        from_str = """
                sale_order s
                join res_partner partner on s.partner_id = partner.id
                left join product_pricelist pp on (s.pricelist_id = pp.id)
                left join currency_rate cr on (cr.currency_id = pp.currency_id and
                    cr.company_id = s.company_id and
                    cr.date_start <= coalesce(s.date_order, now()) and
                    (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
                left join enhanced_reva_tabel r on s.stat_reva = r.id
                left join enhanced_reva_group_tabel rg on r.reva_id = rg.id
                left join project_task pt on s.id = pt.sale_order_id
                left join account_analytic_account ac on s.id = ac.sale_order_id
                left join (select contract_id, sum(amount_untaxed) as amount_untaxed, sum(amount_total) as amount_total from account_invoice where state in ('draft') group by contract_id) ai1 on ac.id = ai1.contract_id
                left join (select contract_id, sum(amount_untaxed) as amount_untaxed, sum(amount_total) as amount_total from account_invoice where state in ('open', 'paid') group by contract_id) ai2 on ac.id = ai2.contract_id
        """
        return from_str

    def _where(self):
        where_str = """
            WHERE s.state not in ('cancel') and jenis_so != 'rental'
        """
        return where_str

    def _where_rental(self):
        where_str = """
            WHERE s.state not in ('cancel') and jenis_so = 'rental'
        """
        return where_str
        # return ""

    def _where_cancel(self):
        where_str = """
            WHERE s.state in ('cancel')
        """
        return where_str

    def _group_by(self):
        group_by_str = """
            GROUP BY s.id,
                    s.jenis_so,
                    s.name,
                    s.date_order,
                    s.confirmation_date,
                    s.bast_date,
                    s.partner_id,
                    s.user_id,
                    s.state,
                    s.company_id,
                    s.pricelist_id,
                    s.cost_center_id,
                    s.analytic_account_id,
                    s.team_id,
                    s.est_invoice_date,
                    s.delivery_doc,
                    s.payment_term_id,
                    s.spk_sementara,
                    s.nomor_spk,
                    s.tgl_spk,
                    s.partner_shipping_id,
                    s.reva_notes,
                    s.nojar,
                    s.proj_type,
                    s.ord_type,
                    s.pek_type,
                    partner.country_id,
                    partner.commercial_partner_id,
                    s.type_reva, r.name, r.reva_id, rg.id,
                    s.requested_date,
                    s.bast_no,
                    s.client_order_ref,
                    pt.create_date::date,
                    pt.daily_tgl_selesai,
                    s.status_stage,
                    s.status_pelaksanaan
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            WITH currency_rate as (%s)
            %s
            FROM ( %s )
            %s
            %s
            UNION
            %s
            FROM ( %s )
            %s
            %s
            UNION
            %s
            FROM ( %s )
            %s
            %s            
            )""" % (self._table, self.env['res.currency']._select_companies_rates(),
                    self._select(), self._from(), self._where(), self._group_by(),
                    self._select_rental(), self._from_rental(), self._where_rental(), self._group_by(),
                    self._select_cancel(), self._from(), self._where_cancel(), self._group_by()))