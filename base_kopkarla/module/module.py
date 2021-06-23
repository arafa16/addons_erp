# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP
#    Copyright (C) 2020 TBD ERP
#
##############################################################################

from odoo import api, fields, models, _

class Module(models.Model):
    _inherit = "ir.module.module"

    license = fields.Selection(selection_add=[('GPL-TBD', 'GPL TBD License')])
