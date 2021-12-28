# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# -*- coding: utf-8 -*-

import time, json
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.http import request
from datetime import datetime as date
import datetime



class AccountCashflowSend(models.TransientModel):
    _name = "account.move.cashflow"
    _description = "Account cashflow"
    _rec_name = "date_from"

    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([]))
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    account_cashflow = fields.Boolean(string="Account Cashflow")
    ref = fields.Char(string="Ref")
    line_ids = fields.One2many('account.move.cashflow.line', 'line_id', string="Line" )
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    display_account = fields.Selection([('all','All'), ('movement','With movements'), 
                                        ('not_zero','With balance is not equal to 0'),], 
                                        string='Display Accounts', required=True, default='movement')

    state = fields.Selection([('draft','Draft'), ('generate','Generated'), ('done','Consolidated'), ('cancel','Cancel')], string="Status", default='draft')

    


class AccountcashflowLineSend(models.TransientModel):
    _name = "account.move.cashflow.line"
    _description = "Account cashflow Line"
    _rec_name = "name"

    line_id = fields.Many2one('account.move.cashflow', string="Line" ,ondelete="cascade")
    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    # debit = fields.Float(string='Debit')
    # credit = fields.Float(string='Credit')
    balance = fields.Float(string='Balance')
