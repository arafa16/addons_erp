# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import os
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class CompanyConsole(models.Model):
    _name = "res.company.console"

    name = fields.Char('Consolidation', required=True)
