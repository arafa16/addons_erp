# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = "account.asset.disposal"

    @api.multi
    def action_disposal_cancel(self):
        for line in self.disposal_line_ids:
            line.asset_id.action_disposal_undo()
        return self.write({'state': 'cancel'})