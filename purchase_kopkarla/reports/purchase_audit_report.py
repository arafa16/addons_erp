# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Please note that these reports are not multi-currency !!!
#

from odoo import api, fields, models, tools


class PurchaseReport(models.Model):
    _name = "purchase.audit.report"
    _description = "Audit Purchases Orders"
    _auto = False
    _order = 'po_date desc'

    so_id = fields.Many2one('sale.order', 'Sales Order', readonly=True)
    so_date = fields.Date('SO Date', readonly=True)
    pr_id = fields.Many2one('sprogroup.purchase.request', 'Purchase Request', readonly=True)
    pr_date = fields.Date('PR Date', readonly=True)
    po_id = fields.Many2one('purchase.order', 'Purchase Order', readonly=True)
    po_date = fields.Date('PO Date', readonly=True)
    inv_id = fields.Char('Invoice', readonly=True)
    inv_date = fields.Date('Invoice Date', readonly=True)
    account_id = fields.Many2one('account.account', 'Account', readonly=True)
    purch_account_id = fields.Many2one('account.account', 'Purchase Account', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft RFQ'),
        ('sent', 'RFQ Sent'),
        ('assmancheck', 'Assman Check'),
        ('requestloa', 'Request LoA'),
        ('loaconfirmed', 'LoA Confirmed'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ], 'Order Status', readonly=True)
    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'No Bill to Receive'),
    ], string='Order Billing Status', readonly=True)
    inv_state = fields.Selection([
            ('draft','Draft'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Billing Status', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    # picking_type_id = fields.Many2one('stock.warehouse', 'Warehouse', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Vendor', readonly=True)
    # date_approve = fields.Date('Date Approved', readonly=True)
    product_uom = fields.Many2one('product.uom', 'Reference Unit of Measure', required=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    user_id = fields.Many2one('res.users', 'Responsible', readonly=True)
    # delay = fields.Float('Days to Validate', digits=(16, 2), readonly=True)
    # delay_pass = fields.Float('Days to Deliver', digits=(16, 2), readonly=True)
    qty_purch = fields.Float('Quantity Purch', readonly=True, oldname='quantity')
    up_purch = fields.Float('Unit Purch', readonly=True)
    amt_purch = fields.Float('Total Purch', readonly=True)
    qty_invoice = fields.Float('Quantity Invoice', readonly=True, oldname='quantity')
    up_invoice = fields.Float('Unit Invoice', readonly=True)
    amt_invoice = fields.Float('Total Invoice', readonly=True)
    # price_average = fields.Float('Average Price', readonly=True, group_operator="avg")
    # negociation = fields.Float('Purchase-Standard Price', readonly=True, group_operator="avg")
    # price_standard = fields.Float('Products Value', readonly=True, group_operator="sum")
    nbr_lines = fields.Integer('# of Lines', readonly=True, oldname='nbr')
    category_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', readonly=True)
    # country_id = fields.Many2one('res.country', 'Partner Country', readonly=True)
    # fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', oldname='fiscal_position', readonly=True)
    cost_center_id = fields.Many2one('cost.center', 'Cost Center', readonly=True)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    # commercial_partner_id = fields.Many2one('res.partner', 'Commercial Entity', readonly=True)
    # weight = fields.Float('Gross Weight', readonly=True)
    # volume = fields.Float('Volume', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'purchase_audit_report')
        self._cr.execute("""
            create view purchase_audit_report as (
                WITH currency_rate as (%s)
                select
                    min(l.id) as id,
                    so.id as so_id, so.date_order::date as so_date,
                    pr.id as pr_id, pr.date_start as pr_date,
                    s.id as po_id, s.date_order::date as po_date,
                    ai.number as inv_id, ai.date as inv_date, ai.state as inv_state, 
                    aa.id as account_id,
                    l.account_id as purch_account_id,
                    s.state,
                    s.invoice_status,
                    s.partner_id as partner_id,
                    s.create_uid as user_id,
                    s.company_id as company_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id as category_id,
                    s.currency_id,
                    t.uom_id as product_uom,
                    count(*) as nbr_lines,
                    sum(l.product_qty/u.factor*u2.factor) as qty_purch,
                    l.price_unit as up_purch,
                    sum(l.price_unit / COALESCE(NULLIF(cr.rate, 0), 1.0) * l.product_qty)::decimal(16,2) as amt_purch,
                    sum(ail.quantity/u.factor*u2.factor) as qty_invoice,
                    ail.price_unit as up_invoice,
                    sum(ail.price_unit / COALESCE(NULLIF(cr.rate, 0), 1.0) * ail.quantity)::decimal(16,2) as amt_invoice,
                    cc.id as cost_center_id,
                    analytic_account.id as account_analytic_id
                from purchase_order_line l
                    join purchase_order s on (l.order_id=s.id)
                    join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                            LEFT JOIN ir_property ip ON (ip.name='standard_price' AND ip.res_id=CONCAT('product.product,',p.id) AND ip.company_id=s.company_id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join cost_center cc on (s.cost_center_id = cc.id)
                    left join account_analytic_account analytic_account on (s.analytic_account_id = analytic_account.id)
                    left join currency_rate cr on (cr.currency_id = s.currency_id and
                        cr.company_id = s.company_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
                left join account_invoice_line ail on l.id = ail.purchase_line_id
                left join account_invoice ai on ail.invoice_id = ai.id
                left join account_account aa on ail.account_id = aa.id
                left join purchase_requisition req on s.requisition_id = req.id
                left join sprogroup_purchase_request pr on req.nomor_pr = pr.id
                left join sale_order so on pr.salesorder_id = so.id
                group by
                    so.id, so.date_order::date,
                    pr.id, pr.date_start,
                    s.id, s.date_order::date,
                    ai.number, ai.date, ai.state, 
                    l.account_id, aa.id,
                    s.company_id,
                    s.create_uid,
                    s.partner_id,
                    u.factor,
                    s.currency_id,
                    l.price_unit,
                    ail.price_unit,
                    l.product_uom,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id,
                    s.date_order,
                    s.state,
                    u.uom_type,
                    u.category_id,
                    t.uom_id,
                    u.id,
                    u2.factor,
                    partner.country_id,
                    partner.commercial_partner_id,
                    cc.id,
                    analytic_account.id
            )
        """ % self.env['res.currency']._select_companies_rates())
