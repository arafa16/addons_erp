# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class Advance(models.Model):
    _name = "hr.advance"
    _inherit = ['hr.advance', 'tier.validation']
    _state_from = ['draft']
    _state_to = ['confirm','approved_hr_manager']

    # def _get_approver_status(self):
    #     for boq in self:
    #         boq.review_inprogress = True #len(self.reviewer_ids.ids) > 0

    # allow_edit = fields.Boolean(compute='_get_allow_edit', default=True)
    #
    # def _get_allow_edit(self):
    #     for travel in self:
    #         if travel.state == 'draft':
    #             if travel.need_validation:
    #                 travel.allow_edit = True
    #             else:
    #                 travel.allow_edit = False
    #         else:
    #             travel.allow_edit = False

    @api.multi
    def validate_tier(self):
        super(Advance, self).validate_tier()
        for rec in self:
            if rec.validated:
                # rec.state = 'posted'
                rec.get_apprv_hr_manager()

    @api.multi
    def reject_tier(self):
        for rec in self:
            user_reviews = rec.review_ids.filtered(lambda r: r.status in ('pending', 'approved'))
            user_reviews.write({
                'status': 'rejected',
                'done_by': self.env.user.id,
                'reviewed_date': fields.Datetime.now(),
            })
            rec._notify_rejected_review()
            rec._update_counter()
            rec.state = 'cancel'

    # def _get_allow_post(self):
    #     for boq in self:
    #         boq.allow_post = ((boq.state == 'draft' and boq.using_mitra) or (boq.state == 'to_rfi' and not boq.using_mitra)) and boq.total_sale and boq.need_validation
    #
    # def _get_allow_cancel(self):
    #     for boq in self:
    #         # boq.allow_cancel = boq.state != 'cancel' and (boq.need_validation or boq.state == 'posted' or boq.total_sale == 0)
    #         boq.allow_cancel = boq.state != 'cancel' # and (boq.need_validation or boq.state == 'posted' or boq.total_sale == 0)

    def get_approval_user(self, level):
        if level < len(self.review_ids):
            return self.review_ids[level].done_by
        return False
