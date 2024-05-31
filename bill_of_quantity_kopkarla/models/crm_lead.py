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