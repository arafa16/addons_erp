# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class InventorySettings(models.TransientModel):

    _inherit = 'res.config.settings'

    inv_cost_ledger = fields.Boolean(string="Inventory Adjustments Ledger Journal", default=True, readonly=False)

    @api.multi
    def set_values(self):
        super(InventorySettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('stock_kopkarla.inv_cost_ledger', self.inv_cost_ledger)

    @api.model
    def get_values(self):
        res = super(InventorySettings, self).get_values()
        res.update({'inv_cost_ledger':bool(self.env['ir.config_parameter'].sudo().get_param('stock_kopkarla.inv_cost_ledger')),})
        return res
