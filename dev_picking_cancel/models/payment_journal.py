# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = "payment.journal"

    @api.multi
    def action_cancel(self):
        for line in self.line_ids:
            line.action_payment_undo()
        return self.write({'state': 'cancelled'})