# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# -*- coding: utf-8 -*-

import time, json
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.http import request
from datetime import datetime as date
import datetime


class Accountcashflow(models.Model):
    _name = "account.cashflow"

    _parent_store = True
    _order = 'code_prefix'

    parent_id = fields.Many2one('account.cashflow', index=True, ondelete='cascade')
    parent_left = fields.Integer('Left Parent', index=True)
    parent_right = fields.Integer('Right Parent', index=True)
    name = fields.Char(required=True)
    code_prefix = fields.Char()

    def name_get(self):
        result = []
        for cashflow in self:
            name = cashflow.name
            if cashflow.code_prefix:
                name = cashflow.code_prefix + ' ' + name
            result.append((cashflow.id, name))
        return result

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     if not args:
    #         args = []
    #     criteria_operator = ['|'] if operator not in expression.NEGATIVE_TERM_OPERATORS else ['&', '!']
    #     domain = criteria_operator + [('code_prefix', '=ilike', name + '%'), ('name', operator, name)]
    #     return self.search(domain + args, limit=limit).name_get()

class AccountAccountInherit (models.Model):
    _inherit     = 'account.account'
    
    cashflow_id = fields.Many2one('account.cashflow', index=True, ondelete='cascade')