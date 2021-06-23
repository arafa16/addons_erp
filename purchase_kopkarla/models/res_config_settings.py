# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_deposit_product_id = fields.Many2one('product.product', 'Deposit Product', domain="[('type', '=', 'service')]")
    allow_force_budget_approve = fields.Boolean('Force Budget Approval')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        default_deposit_product_id = literal_eval(ICPSudo.get_param('purchase_kopkarla.default_deposit_product_id', default='False'))
        if default_deposit_product_id and not self.env['product.product'].browse(default_deposit_product_id).exists():
            default_deposit_product_id = False
        res.update(
            default_deposit_product_id=default_deposit_product_id,
            allow_force_budget_approve=ICPSudo.get_param('allow_force_budget_approve'),
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("purchase_kopkarla.default_deposit_product_id", self.default_deposit_product_id.id)
        ICPSudo.set_param('allow_force_budget_approve', self.allow_force_budget_approve)

