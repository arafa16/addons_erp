# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
    _inherit = "hr.expense.payment.wizard"

    @api.multi
    def expense_post_payment(self):
        return super(HrExpenseSheetRegisterPaymentWizard, self).expense_post_payment()