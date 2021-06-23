# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero, pycompat
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError, ValidationError

import time
import math
import copy

class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.multi
    def populate_journal(self):
        domain = self._prepare_move_line_domain()
        self.create_statement_line_from_move_line(self.env['account.move.line'].search(domain))

    @api.multi
    def _prepare_move_line_domain(self):
        self.ensure_one()
        domain = [('reconciled', '=', False),
                  ('account_id', '=', self.journal_id.default_debit_account_id.id),
                  ('company_id', '=', self.env.user.company_id.id),
                  ('move_id.state', '=', 'posted'),
                  ('blocked', '!=', True),
                  ('date', '<=', self.date),
                  ('statement_line_id', '=', False)]
        return domain

    @api.multi
    def _prepare_statement_line_vals(self, move_line):
        self.ensure_one()
        assert move_line, 'Missing journal'
        amount = move_line.balance
        vals = {
            'name': move_line.name or '?',
            'amount': amount,
            'partner_id': move_line.partner_id.id,
            'statement_id': self.id,
            'ref': move_line.ref,
            'date': move_line.date,
            'amount_currency': move_line.amount_currency,
            'currency_id': move_line.currency_id.id,
            }

        return vals

    @api.multi
    def create_statement_line_from_move_line(self, move_lines):
        abslo = self.env['account.bank.statement.line']
        for mline in move_lines:
            abslo.create(self._prepare_statement_line_vals(mline))