# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import os
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class Users(models.Model):
    _inherit = "res.users"

    console_id = fields.Many2one('res.company.console', string='Consolidation')
