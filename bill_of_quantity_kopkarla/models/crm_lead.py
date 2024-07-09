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

    def create_quotation(self):
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
        #     else:
        #         line = self.contract_id.line_ids[0]
        #         if line:
        #             order_line.append((0, 0, {
        #                 "product_id": line.product_id.id,
        #                 "name": self.contract_id.name,
        #                 "product_uom_qty": 1,
        #                 "product_uom": line.uom_id.id,
        #                 "price_unit": sum(self.contract_id.line_ids.mapped('price_unit')),
        #                 "price_subtotal": sum(self.contract_id.line_ids.mapped('price_unit'))
        #             }))
        # elif self.contract_ids:
        #     line = self.contract_ids[0].line_ids[0]
        #     order_line.append((0, 0, {
        #         "product_id": line.product_id.id,
        #         "name": '%s %s' % (self.service_id.name, self.area_id.name),
        #         "product_uom_qty": 1,
        #         "product_uom": line.uom_id.id,
        #         "price_unit": self.planned_revenue,
        #         # "price_subtotal": sum(self.contract_id.line_ids.mapped('qty')) * line.price_unit
        #     }))
        # order_line.append((0, 0, {
        #     "product_id": line.product_id.id,
        #     "name": self.contract_id.name,
        #     "product_uom_qty": 1,
        #     "product_uom": line.uom_id.id,
        #     "price_unit": sum(self.contract_id.line_ids.mapped('price_unit')),
        #     "price_subtotal": sum(self.contract_id.line_ids.mapped('price_unit'))
        # }))

        # if self.doc_date:
        #     number = self.env['ir.sequence'].with_context({'ir_sequence_date': self.doc_date}).next_by_code('quotation.number')
        # else:
        #     number = self.env['ir.sequence'].next_by_code('quotation.number')
        # area_id = self.env['kamaju.area'].browse(self.area_id.id)
        # number = number.replace("AREA", area_id.code)
        addr = self.partner_id.address_get(['delivery', 'invoice'])
        val = {
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_invoice_id.id or addr['invoice'],
            'partner_shipping_id': self.partner_shipping_id.id or addr['delivery'],
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            # 'customer_code': self.partner_id.ref,
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
            # 'client_order_ref': self.data_customer,
            # 'requested_date': self.doc_date,
            'origin': self.name,
            'opportunity_id': self.id,
            # 'agreement_template_id': self.contract_id.id,
            # 'seq_name': '4%s' % self.name[1:5],
            # 'name': '4%s' % self.name[1:],
            # 'number': number,
            'order_line': order_line,
            # 'spk_no': self.data_customer, # if self.transaction_id.name == 'JOB SUPPLY' else False, # contract_id.name,
            # 'spk_date': self.doc_date, # if self.transaction_id.name == 'JOB SUPPLY' else False,
            # 'bast': self.data_customer, # if self.transaction_id.name == 'JOB SUPPLY' else False, # contract_id.name,
            # 'bast_date': self.doc_date, # if self.transaction_id.name == 'JOB SUPPLY' else False,
        }
        return self.env['sale.order'].create(val)

    @api.multi
    def action_quotations_new(self):
        view_id = self.env.ref('sale.view_order_form')
        order_line = []
        res = self.create_quotation()
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