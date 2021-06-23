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
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

RentalDurationUnits = [
    ('minutes', 'Minute(s)'),
    ('hours', 'Hour(s)'),
    ('days', 'Day(s)'),
    ('weeks', 'Week(s)'),
    ('months', 'Month(s)'),
    ('years', 'Year(s)')
]

class RentalOrderWizard(models.TransientModel):
    # Private attributes
    _name = 'rental.order.wizard'
    _description = 'Wizrad modle to add rental product to SO'

    # Default methods
    def _default_name(self):
        pass

    # Fields declaration
    order_id = fields.Many2one(
        "sale.order", 
        default=lambda self: self._context.get('active_id', False),
        required=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="order_id.pricelist_id.currency_id", 
        string="Currency",
        required=True,
    )
    product_id = fields.Many2one("product.product", string='Rental Product', domain=[('rental_ok', '=', True)], required=True)
    rental_tenure_id = fields.Many2one("product.rental.tenure", default=False)
    quantity = fields.Float('Quantity', required=True, default=1.0)
    rental_tenure_type = fields.Selection(
        [('standard', 'Standard Tenure'), ('custom', 'Custom Tenure')], "Rental Tenure Type", default="standard")
    unit_security_amount = fields.Float(
        'Security Unit Amount', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    rental_uom_id = fields.Many2one("product.uom", "Tenure UOM", required=True, domain=lambda self: [
                                    ('is_rental_uom', '=', True)])
    rental_tenure = fields.Float("Rental Tenure")

    # compute and search fields, in the same order of fields declaration

    # Constraints and onchanges

    @api.multi
    @api.onchange('rental_tenure_id')
    def onchange_rental_tenure_id(self):
        if self.rental_tenure_id:
            self.rental_tenure = self.rental_tenure_id.tenure_value
            self.rental_uom_id = self.rental_tenure_id.rental_uom_id.id


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.quantity,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
            )

            self.unit_security_amount = self.product_id.currency_id.compute(
                self.unit_security_amount or self.product_id.security_amount, self.order_id.pricelist_id.currency_id)
            self.quantity = 1.0
            return {
                'domain': {
                    'rental_tenure_id': [
                        ('id', 'in', product.product_tmpl_id.rental_tenure_ids and product.product_tmpl_id.rental_tenure_ids.ids or [])],
                    'rental_uom_id': [('id', 'in', product.product_tmpl_id.get_applicable_rental_uom_ids())]
                }
            }
        else:
            self.unit_security_amount = 0.0
            self.rental_tenure_id = False
            self.quantity = 0.0
            self.rental_uom_id = False
            self.rental_tenure = 0.0
            return {
                'domain': {
                    'rental_tenure_id': [
                        ('id', 'in', [])],
                    'rental_uom_id': [('id', 'in', [])]
                }
            }

    # CRUD methods (and name_get, name_search, pass) overrides

    # Action methods
    @api.multi
    def action_add_rental_product(self):
        self.ensure_one()
        if self.quantity <= 0:
            raise Warning(_("Qty must be greater than 0."))
        if self.rental_tenure_type == "standard" and not self.rental_tenure_id:
            raise Warning(_("Please select rental tenure scheme for standard type of tenure."))
        if self.rental_tenure <= 0:
            raise Warning(_("Qty must be greater than 0."))
        if self.product_id:
            taxes_ids = []
            if self.product_id.taxes_id:
                taxes_ids = self.product_id.taxes_id.ids
            rental_uom_id = self.rental_uom_id.id
            rental_tenure = self.rental_tenure
            return_value_price_pair = self.product_id.get_product_tenure_price(
                rental_tenure, rental_uom_id, self.rental_tenure_id)
            price_unit = 0.0
            if return_value_price_pair:
                rental_tenure = return_value_price_pair[0]
                price_unit = return_value_price_pair[1]

            sol_values = {
                'order_id': self._context['active_id'],
                'product_id': self.product_id.id,
                'is_rental_order':True,
                'price_unit': self.product_id.currency_id.compute(price_unit, self.order_id.pricelist_id.currency_id),
                'product_uom': 1, #unit
                'product_uom_qty': self.quantity, 
                'tax_id': [(6, 0, taxes_ids)],
                'rental_uom_id': rental_uom_id,
                'rental_tenure': rental_tenure,
                'rental_status': "new",
                'unit_security_amount': self.product_id.currency_id.compute(self.unit_security_amount or self.product_id.security_amount, self.order_id.pricelist_id.currency_id),
            }
            self.env['sale.order.line'].create(sol_values)
            return True

    # Business methods
