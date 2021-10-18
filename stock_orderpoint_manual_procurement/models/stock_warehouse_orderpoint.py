# Copyright 2016-17 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from datetime import datetime
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_round
import operator as py_operator

UNIT = dp.get_precision('Product Unit of Measure')

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    procure_recommended_qty = fields.Float(
        string='Procure Recommendation',
        compute="_compute_procure_recommended",
        digits=UNIT,
    )
    procure_recommended_date = fields.Date(
        string='Recommended Request Date',
        compute="_compute_procure_recommended",
    )

    @api.multi
    def _get_procure_recommended_qty(self, virtual_qty, op_qtys):
        self.ensure_one()
        procure_recommended_qty = 0.0
        qty = max(self.product_min_qty, self.product_max_qty) - virtual_qty
        remainder = \
            self.qty_multiple > 0 and qty % self.qty_multiple or 0.0
        if float_compare(
                remainder, 0.0,
                precision_rounding=self.product_uom.rounding) > 0:
            qty += self.qty_multiple - remainder

        if float_compare(
                qty, 0.0,
                precision_rounding=self.product_uom.rounding) <= 0:
            return procure_recommended_qty

        qty -= op_qtys[self.id]
        qty_rounded = float_round(
            qty, precision_rounding=self.product_uom.rounding)
        if qty_rounded > 0:
            procure_recommended_qty = qty_rounded
        return procure_recommended_qty

    @api.multi
    @api.depends("product_min_qty", "product_id", "qty_multiple")
    def _compute_procure_recommended(self):
        op_qtys = self._quantity_in_progress()
        for op in self:
            qty = 0.0
            virtual_qty = op.with_context(
                location=op.location_id.id).product_id.virtual_available
            if float_compare(virtual_qty, op.product_min_qty,
                             precision_rounding=op.product_uom.rounding) < 0:
                qty = op._get_procure_recommended_qty(virtual_qty, op_qtys)
            op.procure_recommended_qty = qty
            op.procure_recommended_date = op._get_date_planned(
                qty, datetime.today())

    immediately_usable_qty = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_compute_available_quantities',
        search="_search_immediately_usable_qty",
        string='Available to promise',
        help="Stock for this Product that can be safely proposed "
             "for sale to Customers.\n"
             "The definition of this value can be configured to suit "
             "your needs.")
    potential_qty = fields.Float(
        compute='_compute_available_quantities',
        digits=dp.get_precision('Product Unit of Measure'),
        string='Potential',
        help="Quantity of this Product that could be produced using "
             "the materials already at hand.")

    @api.multi
    def _compute_available_quantities_dict(self):
        res = {}
        for product in self:
            stock_dict = product.product_id._compute_quantities_dict(
                product.product_id._context.get('lot_id'),
                product.product_id._context.get('owner_id'),
                product.product_id._context.get('package_id'),
                product.product_id._context.get('from_date'),
                product.product_id._context.get('to_date'))
            res[product.product_id.id] = {
                'immediately_usable_qty': stock_dict[product.product_id.id][
                    'virtual_available'],
                'potential_qty': 0.0
            }
        return res, stock_dict

    @api.multi
    def _compute_available_quantities(self):
        res, _ = self._compute_available_quantities_dict()
        for product in self:
            for key, value in res[product.product_id.id].items():
                if hasattr(product, key):
                    product[key] = value

    @api.model
    def _search_immediately_usable_qty(self, operator, value):
        """ Search function for the immediately_usable_qty field.
        The search is quite similar to the Odoo search about quantity available
        (addons/stock/models/product.py,253; _search_product_quantity function)
        :param operator: str
        :param value: str
        :return: list of tuple (domain)
        """
        products = self.search([])
        # Force prefetch
        products.mapped("immediately_usable_qty")
        product_ids = []
        for product in products:
            if OPERATORS[operator](product.immediately_usable_qty, value):
                product_ids.append(product.id)
        return [('id', 'in', product_ids)]
