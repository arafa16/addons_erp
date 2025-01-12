# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from datetime import datetime
from datetime import timedelta


class TierValidation(models.AbstractModel):
    _inherit = "tier.validation"

    def _notify_requested_review_body(self):
        msg = 'A review has been requested by %s.' % (self.env.user.name)
        if self._name == 'bill.quantity':
            msg += '<br/><br/>BoQ No: %s' % (self.name)
            msg += '<br/>CRM: %s' % (self.crm_id.name)
            msg += '<br/>Total Cost: %s' % (self.total_cost)
            msg += '<br/>Total Sales: %s' % (self.total_sale)
            msg += '<br/>Margin Amount: Rp. %s,-' % (self.margin_amount)
            msg += '<br/>Margin: %s' % (self.margin_pct)
        return msg

    # @api.multi
    # def request_validation(self):
    #     td_obj = self.env['tier.definition']
    #     tr_obj = created_trs = self.env['tier.review']
    #     for rec in self:
    #         if getattr(rec, self._state_field) in self._state_from:
    #             if rec.need_validation:
    #                 tier_definitions = td_obj.search([
    #                     ('model', '=', self._name)], order="sequence desc")
    #                 sequence = 0
    #                 for td in tier_definitions:
    #                     for name, field in rec._fields.items():
    #                         if name == td.reviewer_field_id.name:
    #                             setattr(field, 'copy', False)
    #                             break
    #                     # setattr(getattr(rec, td.reviewer_field_id.name), 'name', '1')
    #                     # getattr(rec, td.reviewer_field_id.name).set('invisible', '1')
    #                     if rec.evaluate_tier(td):
    #                         sequence += 1
    #                         created_trs += tr_obj.create({
    #                             'model': self._name,
    #                             'res_id': rec.id,
    #                             'definition_id': td.id,
    #                             'sequence': sequence,
    #                             'requested_by': self.env.uid,
    #                         })
    #                         setattr(field, 'copy', True)
    #                         # setattr(getattr(rec, td.reviewer_field_id.name), 'invisible', '0')
    #                         # getattr(rec, td.reviewer_field_id.name).set('invisible', '0')
    #                 self._update_counter()
    #     self._notify_review_requested(created_trs)
    #     return created_trs
