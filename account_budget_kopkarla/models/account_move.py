# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def _post_validate(self):
        if self.allow_check_budget():
            self._check_budget()
        return super(AccountMove, self)._post_validate()

    def allow_check_budget(self):
        return self.env['ir.config_parameter'].sudo().get_param('allow_budget_ledger_control', default=False)


    @api.multi
    def _check_budget(self):
        err_msg = []
        for move in self:
            for line in move.line_ids:
                err_msg.append(line._check_budget())

        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def _check_budget(self):
        return True
        # budget_position = self.env['account.budget.post'].sudo()
        # move_line_domain = [
        #     ('res_id', '=', res_id)
        # ]
        #
        # budget = self.env['crossovered.budget.lines'].sudo().search(move_line_filter)
        #
        # if self.date <= (lock_date or '0000-00-00'):
        #     if self.user_has_groups('account.group_account_manager'):
        #         message = _("You cannot add/modify entries prior to and inclusive of the lock date %s") % (lock_date)
        #     else:
        #         message = _(
        #             "You cannot add/modify entries prior to and inclusive of the lock date %s. Check the company settings or ask someone with the 'Adviser' role") % (
        #                       lock_date)
        #     raise UserError(message)