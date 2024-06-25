from odoo import fields, models, tools, api


class OpportunitySaleReport(models.Model):
    _name = "crm.opportunity.sale.report"
    _auto = False
    _description = "CRM Opportunity Sales Analysis"
    _rec_name = 'date_deadline'

    date_deadline = fields.Date('Expected Closing', readonly=True)
    create_date = fields.Datetime('Creation Date', readonly=True)
    opening_date = fields.Datetime('Assignation Date', readonly=True)
    date_closed = fields.Datetime('Close Date', readonly=True)
    # date_last_stage_update = fields.Datetime('Last Stage Update', readonly=True)
    active = fields.Boolean('Active', readonly=True)

    # durations
    # delay_open = fields.Float('Delay to Assign', digits=(16, 2), readonly=True, group_operator="avg", help="Number of Days to open the case")
    # delay_close = fields.Float('Delay to Close', digits=(16, 2), readonly=True, group_operator="avg", help="Number of Days to close the case")
    # delay_expected = fields.Float('Overpassed Deadline', digits=(16, 2), readonly=True, group_operator="avg")

    user_id = fields.Many2one('res.users', string='User', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Channel', oldname='section_id', readonly=True)
    nbr_activities = fields.Integer('# of Activities', readonly=True)
    city = fields.Char('City')
    country_id = fields.Many2one('res.country', string='Country', readonly=True)
    probability = fields.Float(string='Probability', digits=(16, 2), readonly=True, group_operator="avg")
    total_revenue = fields.Float(string='Total Revenue', digits=(16, 2), readonly=True)
    expected_revenue = fields.Float(string='Probable Turnover', digits=(16, 2), readonly=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', readonly=True, domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]")
    stage_name = fields.Char(string='Stage Name', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    # company_id = fields.Many2one('res.company', string='Company', readonly=True)
    # priority = fields.Selection(crm_stage.AVAILABLE_PRIORITIES, string='Priority', group_operator="avg")
    # type = fields.Selection([
    #     ('lead', 'Lead'),
    #     ('opportunity', 'Opportunity'),
    # ], help="Type is used to separate Leads and Opportunities")
    # lost_reason = fields.Many2one('crm.lost.reason', string='Lost Reason', readonly=True)
    # date_conversion = fields.Datetime(string='Conversion Date', readonly=True)
    # campaign_id = fields.Many2one('utm.campaign', string='Campaign', readonly=True)
    # source_id = fields.Many2one('utm.source', string='Source', readonly=True)
    # medium_id = fields.Many2one('utm.medium', string='Medium', readonly=True)

    order_type_id = fields.Many2one('crm.order.type', 'Order Type', required=True, track_visibility='onchange')
    proj_type_id = fields.Many2one('enhanced.sales.project.tabel', string='Jenis Project', track_visibility='onchange')
    area_id = fields.Many2one('enhanced.sales.area', string='Sales Area', required=True)
    sale_order = fields.Char('Sales Order', readonly=True)
    order_date = fields.Datetime('Date Order', readonly=True)
    confirmation_date = fields.Datetime('Confirmation Date', readonly=True)
    order_state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('spvcheck', 'SPV Check'),
        ('assmancheck', 'Assman Check'),
        ('requestloa', 'Request LoA'),
        ('loaconfirmed', 'LoA Confirmed'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)

    product_uom_qty = fields.Float('Qty Ordered', readonly=True)
    qty_delivered = fields.Float('Qty Delivered', readonly=True)
    qty_to_invoice = fields.Float('Qty To Invoice', readonly=True)
    qty_invoiced = fields.Float('Qty Invoiced', readonly=True)
    price_total = fields.Float('Total', readonly=True)
    price_subtotal = fields.Float('Untaxed Total', readonly=True)
    amt_to_invoice = fields.Float('Amount To Invoice', readonly=True)
    amt_invoiced = fields.Float('Amount Invoiced', readonly=True)

    def _select(self):
        select_str = """
SELECT  c.id,
        c.date_deadline,
        c.date_open as opening_date,
        c.date_closed as date_closed,
--         c.date_last_stage_update as date_last_stage_update,
        c.user_id,
        c.probability,
        c.stage_id,
        stage.name as stage_name,
--         c.type,
--         c.company_id,
--         c.priority,
        c.team_id,
--         (SELECT COUNT(*)
--          FROM mail_message m
--          WHERE m.model = 'crm.lead' and m.res_id = c.id) as nbr_activities,
        c.active,
--         c.campaign_id,
--         c.source_id,
--         c.medium_id,
        c.partner_id,
--         c.city,
--         c.country_id,
        c.planned_revenue as total_revenue,
        c.planned_revenue * (c.probability/100) as expected_revenue,
        c.create_date as create_date,
--         extract('epoch' from (c.date_closed-c.create_date))/(3600*24) as  delay_close,
--         abs(extract('epoch' from (c.date_deadline - c.date_closed))/(3600*24)) as  delay_expected,
--         extract('epoch' from (c.date_open-c.create_date))/(3600*24) as  delay_open,
--         c.lost_reason,
--         c.date_conversion as date_conversion,
        c.order_type_id,
        c.proj_type_id,
        c.area_id,
        s.name as sale_order,
        s.date_order as order_date,
        s.confirmation_date as confirmation_date,
        s.state as order_state,
        sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
        sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
        sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
        sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
        sum(l.price_total) as price_total,
        sum(l.price_subtotal) as price_subtotal,
        sum(l.amt_to_invoice) as amt_to_invoice,
        sum(l.amt_invoiced) as amt_invoiced
        """
        return select_str

    def _from(self):
        from_str = """
FROM "crm_lead" c
        """
        return from_str

    def _join(self):
        join_str = """
LEFT JOIN "crm_stage" stage ON stage.id = c.stage_id
LEFT JOIN "sale_order" s ON s.opportunity_id = c.id
LEFT JOIN "sale_order_line" l ON l.order_id = s.id
LEFT JOIN product_product p ON l.product_id = p.id
LEFT JOIN product_template t ON p.product_tmpl_id = t.id
LEFT JOIN product_uom u ON u.id = l.product_uom
LEFT JOIN product_uom u2 ON u2.id = t.uom_id
LEFT JOIN product_pricelist pp ON s.pricelist_id = pp.id
        """
        return join_str

    def _where(self):
        where_str = """
        """
        return where_str

    def _group_by(self):
        group_by_str = """
            GROUP BY c.id, stage.name, s.name, s.date_order, s.confirmation_date, s.state
        """
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE VIEW %s AS (
            %s
            %s
            %s
            %s
            %s
        )""" % (self._table, self._select(), self._from(), self._join(), self._where(), self._group_by()))
