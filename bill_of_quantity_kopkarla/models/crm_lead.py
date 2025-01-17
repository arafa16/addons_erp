# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError


class Lead(models.Model):
    _inherit = "crm.lead"

    boq_ids = fields.One2many('bill.quantity', 'crm_id', 'Bill of Quantity')
    boq_count = fields.Integer('BoQ', compute='_get_boq_count')
    boq_id = fields.Many2one('bill.quantity', 'Bill of Quantity')
    rfi_expired_date = fields.Date('BoQ Expired Date', related='boq_id.rfi_expired_date')
    boq_rfi_expired = fields.Boolean('BoQ Expired', compute='_get_boq_rfi_expired')
    boq_amount = fields.Float('Biaya Mitra', related='boq_id.total_cost')
    overhead_amount = fields.Float('Biaya Overhead', compute='_calc_amount')
    total_cost = fields.Float('Total Cost', compute='_calc_amount')
    total_sale = fields.Float('Total SPH', related='boq_id.total_sale')
    margin_amount = fields.Float('Margin Amount', compute='_calc_amount')
    margin_pct = fields.Float('Margin', compute='_calc_amount')

    def quotation_values(self):
        order_line = []
        if self.order_type_id. name == 'Trading':
            for boq in self.boq_ids.filtered(lambda b: b.state == 'posted'):
                for line in boq.line_material_ids:
                    order_line.append((0, 0, {
                        "product_id": line.product_id.id,
                        "name": line.name,
                        "product_uom_qty": line.qty,
                        "product_uom": line.uom_id.id,
                        "price_unit": line.sale_price,
                        # "price_subtotal": sum(self.contract_id.line_ids.mapped('qty')) * line.price_unit
                    }))
                if order_line:
                    break
        addr = self.partner_id.address_get(['delivery', 'invoice'])
        val = {
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_invoice_id.id or addr['invoice'],
            'partner_shipping_id': self.partner_shipping_id.id or addr['delivery'],
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'team_id': self.team_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'user_id': self.user_id.id,
            'jenis_so': self.jenis_so,
            'proj_type': self.proj_type_id.id,
            'so_bagian': self.department_id.id,
            'sales_area_kode': self.area_id.id,

            'cost_center_id': self.cost_center_id.id,
            'analytic_account_id': self.analytic_account_id.id,
            'origin': self.name,
            'opportunity_id': self.id,
            'order_line': order_line,
        }
        return val

    @api.multi
    def action_quotations_new(self):
        view_id = self.env.ref('sale.view_order_form')
        # order_line = []
        res = self.env['sale.order'].create(self.quotation_values())
        return {
            'name': _("New Quotation"),
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'view_id': view_id.id,
            # 'context': context_val,
            'res_id': res.id,
            'context': {'form_view_initial_mode': 'edit', 'force_detailed_view': 'true'},
        }

    def _get_boq_rfi_expired(self):
        for lead in self:
            if lead.rfi_expired_date:
                lead.boq_rfi_expired = lead.rfi_expired_date < fields.Datetime.now()
            else:
                lead.boq_rfi_expired = False

    def _calc_amount(self):
        for lead in self:
            lead.overhead_amount = lead.overhead_pct * lead.boq_amount / 100
            lead.total_cost = lead.boq_amount + lead.overhead_amount
            lead.margin_amount = lead.total_sale - lead.total_cost
            lead.margin_pct = (lead.margin_amount / lead.total_sale * 100) if lead.total_sale != 0 else 0

    def _get_boq_count(self):
        for lead in self:
            lead.boq_count = len(lead.boq_ids)

    @api.onchange('boq_id','revenue_margin')
    def _onchange_boq(self):
        self.planned_revenue = 0
        self.overhead_amount = 0
        self.total_cost = 0
        self.margin_amount = 0
        self.margin_pct = 0
        if self.boq_id:
            # self.planned_revenue = self.boq_amount * (1 + self.revenue_margin / 100)
            self.planned_revenue = self.total_sale #* (1 + self.revenue_margin / 100)
            self._calc_amount()