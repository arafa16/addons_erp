# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import api, fields, models, _ 

import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Fields declaration

    is_rental_picking = fields.Boolean(
        "Is Rental Picking", 
        compute="_compute_rental_so", 
        store=True,
    )
    
    # compute and search fields, in the same order of fields declaration

    @api.multi
    @api.depends('move_lines.rental_contract_ids')
    def _compute_rental_so(self):
        for picking in self:
            if picking.move_lines and picking.move_lines.filtered("rental_contract_ids"):
                picking.is_rental_picking = True


class StockMove(models.Model):
    _inherit = "stock.move"

    # Fields declaration

    rental_contract_ids = fields.Many2many(
        "rental.order.contract", 
        "rental_stock_move_contract_id", 
        "stock_move_id", 
        "contract_id", 
        "Rental Contracts",
    )


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        if values.get('sale_line_id', False) or result.get('sale_line_id', False):
            sol_obj = self.env["sale.order.line"].browse(
                values.get('sale_line_id') or result.get('sale_line_id', False))
            if self._context.get("contract_id", False):
                result['rental_contract_ids'] = [(6, 0, [self._context.get("contract_id")])]
            else:
                if len(sol_obj.rental_contract_ids) == 1:
                    result['rental_contract_ids'] = [(6, 0, [sol_obj.inital_rental_contract_id and sol_obj.inital_rental_contract_id.id])]
                elif len(sol_obj.rental_contract_ids) > 1:
                    result['rental_contract_ids'] = [(6, 0, [sol_obj.current_rental_contract_id and sol_obj.current_rental_contract_id.id])]
        return result
