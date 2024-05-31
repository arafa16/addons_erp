# Copyright 2019 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TierReview(models.Model):
    _inherit = "tier.review"

    reviewer_field_id = fields.Many2one(
        related="definition_id.reviewer_field_id", readonly=True
    )
    reviewer_ids = fields.Many2many(
        string="Reviewers",
        comodel_name="res.users",
        compute="_compute_reviewer_ids",
        store=True,
    )

    @api.model
    def _get_reviewer_fields(self):
        return ["reviewer_id", "reviewer_group_id", "reviewer_group_id.users"]

    @api.depends(lambda self: self._get_reviewer_fields())
    def _compute_reviewer_ids(self):
        for rec in self:
            rec.reviewer_ids = rec._get_reviewers()

    @api.depends("reviewer_ids")
    def _compute_todo_by(self):
        """Show by group or by abbrev list of names"""
        num_show = 3  # Max number of users to display
        for rec in self:
            todo_by = False
            if rec.reviewer_group_id:
                todo_by = _("Group %s") % rec.reviewer_group_id.name
            else:
                todo_by = ", ".join(rec.reviewer_ids[:num_show].mapped("display_name"))
                num_users = len(rec.reviewer_ids)
                if num_users > num_show:
                    todo_by = "{} (and {} more)".format(todo_by, num_users - num_show)
            rec.todo_by = todo_by

    def _get_reviewers(self):
        if self.reviewer_id or self.reviewer_group_id.users:
            return self.reviewer_id + self.reviewer_group_id.users
        reviewer_field = self.env["res.users"]
        if self.reviewer_field_id:
            resource = self.env[self.model].browse(self.res_id)
            reviewer_field = getattr(resource, self.reviewer_field_id.name, False)
            if not reviewer_field or not reviewer_field._name == "res.users":
                raise ValidationError(_("There are no res.users in the selected field"))
        return reviewer_field
