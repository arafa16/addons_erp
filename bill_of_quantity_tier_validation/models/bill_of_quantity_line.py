from odoo import models, fields, api, _
from datetime import datetime


class bill_quantity_line(models.Model):
    _inherit = 'bill.quantity.line'

    def _get_allow_set_vendor(self):
        for line in self:
            line.allow_set_vendor = line.state == 'done' and line.rfi_send and (line.bill_quantity_id.need_validation or line.bill_quantity_id.total_sale == 0)

    def _get_allow_set_sales(self):
        for line in self:
            line.allow_set_sales = line.bill_quantity_id.allow_post or not line.bill_quantity_id.total_sale or line.bill_quantity_id.need_validation
