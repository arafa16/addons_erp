# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = "account.asset.revaluation"

    @api.multi
    def action_revaluation_cancel(self):
        for line in self.revaluation_line_ids:
            line.action_revaluation_undo()
        return self.write({'state': 'cancel'})