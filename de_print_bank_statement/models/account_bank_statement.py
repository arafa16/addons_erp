# -*- coding: utf-8 -*-
from odoo import models

class PrintBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def print_bank_statement(self):
        return self.env.ref('de_print_bank_statement.action_statement_report').report_action(self)
