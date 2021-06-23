# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solutions.(<https://tidyway.in/>)

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class TenderReport(models.TransientModel):
    _name = 'tender.report'

    condition = fields.Selection([
              ('min_three', 'Compare Lowest To Highest Quotation Prices'),
              ('max_three', 'Compare Highest To Lowest Quotation Prices')
              ],
             string="Price Comparision Type",
             required=True,
             default="min_three")

    @api.model
    def _check_validation(self):
        if not self.env.user.has_group('purchase_tender_report.group_purchase_requisition_report'):
            raise Warning(_(' You have not enough rights to access this '
                            'report, please contact administrator to '
                            'access this report.'))

    @api.multi
    def print_pdf(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        self._check_validation()
        requisition_ids = self._context.get('active_ids', []) or []
        datas = {
                 'ids': requisition_ids,
                 'form':
                        {
                            'condition': self.condition,
                        }
                }

        return self.env.ref(
                            'purchase_tender_report.menu_tender_comparision_report'
                            ).with_context(landscape=True).report_action(self, data=datas)

    @api.multi
    def print_xls(self):
        pass
