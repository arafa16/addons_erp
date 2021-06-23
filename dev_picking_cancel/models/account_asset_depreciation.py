# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = "account.asset.depreciation"

    @api.multi
    def action_depreciation_cancel(self):
        self.action_depreciation_undo()
        # for line in self.depreciation_line_ids:
        #     line.action_depreciation_undo()
        return self.write({'state': 'cancel'})