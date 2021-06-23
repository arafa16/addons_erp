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
from datetime import datetime
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class RenewRentalOrderWizard(models.TransientModel):
    # Private attributes
    _name = 'rental.order.renew.wizard'
    _description = 'Wizrad model to renew rental order'

    # Default methods
    @api.model
    def _get_rental_sol_id(self):
        sol_id = self.env['sale.order.line'].browse(self._context['active_id'])
        return sol_id.id if sol_id else False

    @api.model
    def _get_rental_product_agreement(self):
        sol_id = self.env['sale.order.line'].browse(self._context['active_id'])
        return sol_id.product_id.rental_agreement_id.id if sol_id and sol_id.product_id.rental_agreement_id else False

    @api.model
    def _get_rental_quantity(self):
        sol_id = self.env['sale.order.line'].browse(self._context['active_id'])
        return sol_id.product_uom_qty if sol_id else False

    @api.model
    def _get_rental_uom_id(self):
        sol_id = self.env['sale.order.line'].browse(self._context['active_id'])
        return sol_id.rental_uom_id.id if sol_id else False
    
    @api.model
    def _get_rental_rental_uom_ids(self):
        if self.rental_product_id:
            return self.rental_product_id.get_applicable_rental_uom_ids()
        return []

    # Fields declaration
    sale_order_line_id = fields.Many2one(
        "sale.order.line", 
        "Sale Order Line", 
        required=True, 
        default=_get_rental_sol_id,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="sale_order_line_id.order_id.pricelist_id.currency_id",
        string="Currency",
        required=True,
    )
    rental_product_id = fields.Many2one(
        'product.product',
        related='sale_order_line_id.product_id',
        string="Rental Product",
        readonly=True
    )
    rental_customer_id = fields.Many2one(
        'res.partner',
        related='sale_order_line_id.order_id.partner_id',
        string="Customer",
        readonly=True
    )
    product_rental_agreement_id = fields.Many2one(
        "rental.product.agreement", 
        "Rental Agreement", 
        required=True, 
        default=_get_rental_product_agreement,
    )
    rental_qty = fields.Float(
        "Rental Qty", 
        required=True, 
        default=_get_rental_quantity,
    )
    rental_tenure_type = fields.Selection(
        [('standard', 'Standard Tenure'), ('custom', 'Custom Tenure')], 
        "Rental Tenure Type", 
        default="standard",
    )
    rental_uom_id = fields.Many2one(
        "product.uom", 
        "Tenure UOM", 
        required=True, 
        domain=lambda self: [('is_rental_uom', '=', True)],
    )
    unit_security_amount = fields.Float(
        'Security Unit Amount', 
        required=True, 
        digits=dp.get_precision('Product Price'), 
        default=0.0,
    )
    rental_tenure = fields.Float("Rental Tenure")
    rental_tenure_id = fields.Many2one(
        "product.rental.tenure", 
        default=False,
    )

    # compute and search fields, in the same order of fields declaration

    # Constraints and onchanges

    @api.multi
    @api.onchange('sale_order_line_id')
    def product_id_change(self):
        return {
            'domain': {
                'rental_tenure_id': [
                    ('id', 'in', self.rental_product_id.product_tmpl_id.rental_tenure_ids and self.rental_product_id.product_tmpl_id.rental_tenure_ids.ids or [])],
                'rental_uom_id': [('id', 'in', self.rental_product_id.product_tmpl_id.get_applicable_rental_uom_ids())]
            }
        }

    @api.multi
    @api.onchange('rental_tenure_id')
    def onchange_rental_tenure_id(self):
        if self.rental_tenure_id:
            self.rental_tenure = self.rental_tenure_id.tenure_value
            self.rental_uom_id = self.rental_tenure_id.rental_uom_id.id

    # CRUD methods (and name_get, name_search, pass) overrides

    # Action methods

    @api.multi
    def action_create_rental_contract(self):
        self.ensure_one()
        if self.rental_qty <= 0:
            raise Warning(_("Qty must be greater than 0."))
        if self.rental_tenure_type == "standard" and not self.rental_tenure_id:
            raise Warning(
                _("Please select rental tenure scheme for standard type of tenure."))
        if self.rental_tenure <= 0:
            raise Warning(_("Qty must be greater than 0."))
        if self.rental_product_id:
            taxes_ids = []
            if self.rental_product_id.taxes_id:
                taxes_ids = self.rental_product_id.taxes_id.ids
            rental_uom_id = self.rental_uom_id.id
            rental_tenure = self.rental_tenure
            return_value_price_pair = self.rental_product_id.get_product_tenure_price(
                rental_tenure, rental_uom_id)
            price_unit = 0.0
            if return_value_price_pair:
                rental_tenure = return_value_price_pair[0]
                price_unit = return_value_price_pair[1]

            ro_contract_values = {
                'sale_order_line_id': self.sale_order_line_id.id,
                'product_rental_agreement_id': self.product_rental_agreement_id.id,
                'price_unit': self.sale_order_line_id.product_id.currency_id.compute(price_unit, self.sale_order_line_id.order_id.pricelist_id.currency_id),
                'rental_qty': self.rental_qty,
                'rental_uom_id': rental_uom_id,
                'rental_tenure': rental_tenure,
                'tax_ids': [(6, 0, taxes_ids)],
                'is_renewal_contract': True,
            }
            new_created_rental_contract = self.env['rental.order.contract'].create(
                ro_contract_values)
            new_created_rental_contract.action_confirm()
            if new_created_rental_contract and len(self.sale_order_line_id.rental_contract_ids) == 1:
                self.sale_order_line_id.inital_rental_contract_id = new_created_rental_contract.id
            else:
                contract_to_check = False
                if self.sale_order_line_id.current_rental_contract_id:
                    contract_to_check = self.sale_order_line_id.current_rental_contract_id
                else:
                    contract_to_check = self.sale_order_line_id.inital_rental_contract_id
                if contract_to_check and not (contract_to_check.check_product_received()):
                    #code to link current contract done move to latest contrcat
                    new_created_rental_contract.link_move_to_new_contract(
                        contract_to_check, new_created_rental_contract)
                    new_created_rental_contract.start_time = fields.datetime.now()
                    self.sale_order_line_id.current_start_time = new_created_rental_contract.start_time
                self.sale_order_line_id.write({
                    "current_rental_contract_id": new_created_rental_contract.id,
                    "last_renewal_time": datetime.now(),
                })
            view_id = self.env.ref('odoo_sale_rental.rental_order_contract_view_form').id
            return {
                'name': 'Rental Contract',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'res_model': 'rental.order.contract',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'res_id': new_created_rental_contract.id,
            }
            return True

    # Business methods
