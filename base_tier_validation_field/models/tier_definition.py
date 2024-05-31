# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, api, models


class TierDefinition(models.Model):
    _inherit = 'tier.definition'

    review_type = fields.Selection(
        selection_add=[("field", "Field in related record")]
    )
    reviewer_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Reviewer field",
        domain="[('id', 'in', valid_reviewer_field_ids)]",
    )
    valid_reviewer_field_ids = fields.One2many(
        comodel_name="ir.model.fields",
        compute="_compute_domain_reviewer_field",
    )

    @api.depends("review_type", "model_id")
    def _compute_domain_reviewer_field(self):
        for rec in self:
            rec.valid_reviewer_field_ids = self.env["ir.model.fields"].search(
                [("model", "=", rec.model), ("relation", "=", "res.users")]
            )
