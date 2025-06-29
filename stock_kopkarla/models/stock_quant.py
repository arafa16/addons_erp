# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from psycopg2 import OperationalError, Error

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero

import logging

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.multi
    def write(self, vals):
        res = super(StockQuant, self).write(vals)
        rule_id = self.env['stock.warehouse.orderpoint'].sudo().search([('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])
        if rule_id and self.quantity < rule_id.product_min_qty:
            rule_id.send_notification_below_minimum_stock()
        return res
