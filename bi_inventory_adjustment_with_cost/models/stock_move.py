from datetime import datetime
from dateutil import relativedelta
from itertools import groupby
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    total_price = fields.Float(string='Total', compute='_compute_cost_price')

    def _compute_cost_price(self):
        for move in self:
            move.total_price = move.price_unit * move.product_uom_qty
