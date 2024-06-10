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

    def _get_domain_presales(self):
        group_presales_id = self.sudo().env.ref('crm_kopkarla.group_presales').id
        return [('groups_id', 'in', [group_presales_id])]

    # order_type = fields.Selection([("PNR", "Project Non Reguler"),
    #                                ("FO", "Project FO Lastmile"),
    #                                ("trading", "Trading"),
    #                                ("rental", "Rental Order")], string='Order Type')
    order_type_id = fields.Many2one('crm.order.type', 'Order Type', required=True, track_visibility='onchange')
    jenis_so = fields.Selection([("common", "General Order"), ("Project", "Project"), ("datacom", "Trading Datacom"), ("rental", "Rental Order")], related='order_type_id.jenis_so', string='Mapped Type', track_visibility='onchange')
    rental_type = fields.Selection([('Sewa Beli', 'Sewa Beli'), ('Sewa Pakai', 'Sewa Pakai'), ('Back to Back', 'Back to Back'),], 'Rental Type', track_visibility='onchange')
    is_rental = fields.Boolean(related='order_type_id.is_rental')
    proj_type_id = fields.Many2one('enhanced.sales.project.tabel', string='Jenis Project', track_visibility='onchange')
    proj_type_readonly = fields.Boolean()
    need_spk = fields.Boolean(related='order_type_id.need_spk', store=True)
    overhead_pct = fields.Float('Persentase Overhead', related='order_type_id.overhead_pct')
    no_jar = fields.Char('Nomer Jaringan')
    spk = fields.Char('SPK')
    # boq_due = fields.Selection([('1', '1 Hari Kerja'), ('2', '2 Hari Kerja'), ('3', '3 Hari Kerja')], 'BoQ Due Date')
    boq_due_date = fields.Date('BoQ Due Date')
    cost_center_id = fields.Many2one("cost.center", string="Cost Center")
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account') #, required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    area_id = fields.Many2one('enhanced.sales.area', string='Sales Area', required=True)
    end_user = fields.Char('End User')
    end_user_address = fields.Char('Alamat End User')
    presales_user_id = fields.Many2one('res.users', string='Presales Person', index=True, track_visibility='onchange', domain=_get_domain_presales)
    line_material_ids = fields.One2many('crm.lead.line', 'crm_id', string='Material', copy=True)

    @api.onchange('order_type_id')
    def _onchange_order_type(self):
        for lead in self:
            if lead.order_type_id:
                lead.boq_due = lead.order_type_id.boq_due
                lead.proj_type_id = lead.order_type_id.proj_type_id.id
            else:
                lead.boq_due = False
                lead.proj_type_id = False
            lead.proj_type_readonly = lead.proj_type_id

    @api.onchange('area_id')
    def _onchange_area(self):
        self.analytic_account_id = False
        if self.area_id:
            self.analytic_account_id = self.area_id.analytic_account_id.id

    @api.model
    def _onchange_user_values(self, user_id):
        values = super(Lead, self)._onchange_user_values(user_id)
        if self.user_id:
            employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.user_id.id)])
            if employee_id.department_id:
                if employee_id.department_id.adadiSO:
                    values.update({'department_id': employee_id.department_id.id})
                if employee_id.cost_center_id:
                    values.update({'cost_center_id': employee_id.cost_center_id.id})
        return values

    @api.depends('order_ids')
    def _compute_sale_amount_total(self):
        for lead in self:
            total = 0.0
            nbr = 0
            company_currency = lead.company_currency or self.env.user.company_id.currency_id
            for order in lead.order_ids:
                if order.state in ('draft','spvcheck','assmancheck','requestloa','loaconfirmed','sent'):
                    nbr += 1
                if order.state not in ('draft','spvcheck','assmancheck','requestloa','loaconfirmed','sent','cancel'):
                    total += order.currency_id.compute(order.amount_untaxed, company_currency)
            lead.sale_amount_total = total
            lead.sale_number = nbr
