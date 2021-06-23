# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import float_compare

class AccountMoveLine(models.Model):
    _inherit = "account.move"

    def remove_reconcile(self):
        self.line_ids.filtered(lambda x: x.reconciled == True).remove_move_reconcile()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        res = super(AccountMoveLine, self).reconcile(writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        account_move_ids = [l.move_id.id for l in self if float_compare(l.move_id.matched_percentage, 1, precision_digits=5) == 0]
        if account_move_ids:
            expense_sheets = self.env['hr.expense.sheet'].search([
                ('account_move_id', 'in', account_move_ids), ('state', '!=', 'done')
            ])
            payment_ids = self.mapped('payment_id')
            for payment_id in payment_ids:
                expense_sheets.set_to_paid(payment_id.id)
        return res
