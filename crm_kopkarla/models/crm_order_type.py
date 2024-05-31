# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError


class Order_Type(models.Model):
    _name = "crm.order.type"
    _description = 'Order Type'

    name = fields.Char('Order Type')
    proj_type_id = fields.Many2one('enhanced.sales.project.tabel', string='Jenis Project')
    jenis_so = fields.Selection([("common", "General Order"), ("Project", "Project"), ("datacom", "Trading Datacom"), ("rental", "Rental Order")], string='Mapped Type')
    boq_due = fields.Selection([('1', '1 Hari Kerja'), ('2', '2 Hari Kerja'), ('3', '3 Hari Kerja')])
    need_spk = fields.Boolean('SPK')
    using_mitra = fields.Boolean('BoQ Mitra')
    overhead_pct = fields.Float('Overhead (%)')
    is_rental = fields.Boolean('Rental')

