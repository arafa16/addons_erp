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


class RentalReasonWizard(models.TransientModel):
    _name = 'rental.reason.wizard'

    # Default methods

    @api.model
    def _get_rental_contract(self):
        sol_id = self._context.get('active_id', False)
        if sol_id:
            sol_obj = self.env["sale.order.line"].browse(sol_id)
            if sol_obj and sol_obj.current_rental_contract_id:
                return sol_obj.current_rental_contract_id.id
            else:
                return sol_obj.inital_rental_contract_id and sol_obj.inital_rental_contract_id.id

    # Fields declaration

    rental_contract_id = fields.Many2one(
        "rental.order.contract", 
        string="Rental Contract", 
        default=_get_rental_contract,
    )
    reason_id = fields.Many2one(
        "rental.reason", 
        string="Reason", 
        required="1",
    )
    additional_comment = fields.Text(string="Additional Comment")

    # Action methods
    
    @api.multi
    def do_cancel(self):
        self.ensure_one()
        # raise Warning("Canceling reason")
        if self.rental_contract_id:
            self.rental_contract_id.sale_order_line_id.rental_state = "cancel"
            reason_msg = "Cancel Reason : " + self.reason_id.name + "\n" + \
                self.reason_id.description + "\n" + self.additional_comment
            self.rental_contract_id.message_post(
                reason_msg, subtype='mail.mt_comment', message_type='comment')
