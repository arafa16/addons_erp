# Copyright 2014 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Report(models.Model):
    _inherit = "ir.actions.report"

    def render_qweb_pdf(self, res_ids=None, data=None):
        if self.report_name == "sale.report_saleorder":
            if not res_ids:
                res_ids = self.env.context.get("active_ids")
            so_report_instance = self.env["sale.order"].browse(res_ids)[0]
            # context = dict(
            #     pr_report_instance._context_with_filters(),
            #     landscape=pr_report_instance.landscape_pdf,
            # )
            # # data=None, because it was there only to force Odoo
            # # to propagate context
            # return super(Report, self.with_context(context)).render_qweb_pdf(
            #     res_ids, data=None
            # )
            if so_report_instance.state not in ('loaconfirmed', 'sent', 'sale', 'done'):
                raise UserError("SO tidak bisa di cetak karena status belum LoA Confirmed!")
            return super(Report, self).render_qweb_pdf(
                res_ids, data=None
            )
        return super(Report, self).render_qweb_pdf(res_ids, data)
