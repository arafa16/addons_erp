# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = "account.asset.reclass.table"

    @api.multi
    def action_reclass_cancel(self):
        for line in self.reclass_line_ids:
            line.asset_id.action_reclass_undo(line.asset_id_to, line.category_id_to, line.category_id)
            old_values = {
                'category_id': line.category_id_to.id,
                'method_number': line.category_id_to.method_number,
                'method_period': line.category_id_to.method_period,
            }
            asset_vals = {
                'category_id': line.category_id.id,
                'method_number': line.category_id.method_number,
                'method_period': line.category_id.method_period,
            }
            line.asset_id.write(asset_vals)
            line.asset_id.compute_depreciation_board()
            tracked_fields = self.env['account.asset.asset'].fields_get(['category', 'method_number', 'method_period'])
            changes, tracking_value_ids = line.asset_id._message_track(tracked_fields, old_values)
            if changes:
                line.asset_id.message_post(subject=_('Depreciation board modified'), body=self.name,
                                           tracking_value_ids=tracking_value_ids)
        return self.write({'state': 'cancel'})