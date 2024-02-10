# Copyright 2014 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Report(models.Model):
    _inherit = "ir.actions.report"

    def render_qweb_pdf(self, res_ids=None, data=None):
        if self.report_name == "enhanced_purchase_request.template_purchase_request_dokumen":
            if not res_ids:
                res_ids = self.env.context.get("active_ids")
            pr_report_instance = self.env["sprogroup.purchase.request"].browse(res_ids)[0]
            # context = dict(
            #     pr_report_instance._context_with_filters(),
            #     landscape=pr_report_instance.landscape_pdf,
            # )
            # # data=None, because it was there only to force Odoo
            # # to propagate context
            # return super(Report, self.with_context(context)).render_qweb_pdf(
            #     res_ids, data=None
            # )
            if pr_report_instance.state not in ('leader_approved', 'done'):
                raise UserError("Status PR belum LoA Approved atau Procure Received!")
            return super(Report, self).render_qweb_pdf(
                res_ids, data=None
            )
        return super(Report, self).render_qweb_pdf(res_ids, data)
