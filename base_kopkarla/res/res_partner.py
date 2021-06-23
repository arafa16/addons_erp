# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP
#    Copyright (C) 2020 TBD ERP
#
##############################################################################

from odoo import fields, models, _


class Partner(models.Model):
    _inherit = "res.partner"

    vat = fields.Char(string='NPWP', help="Tax Identification Number. "
                                         "Fill it if the company is subjected to taxes. "
                                         "Used by the some of the legal statements.")

    # _sql_constraints = [
    #     ('field_unique',
    #      'unique(vat)',
    #      'Choose another value - it has to be unique!')
    # ]