# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP
#    Copyright (C) 2020 TBD ERP
#
##############################################################################

from odoo import fields, models, _


class Company(models.Model):
    _inherit = "res.company"

    vat = fields.Char(related='partner_id.vat', string="NPWP")
