# Copyright 2017 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class Bill_Quantity(models.Model):
    _inherit = "bill.quantity"

    # review_inprogress = fields.Boolean(compute="get_approver_status", store=True)
    approver1_id = fields.Many2one(comodel_name="res.users", string="Approver 1", domain=lambda self: self._get_approval1_domain())
    approver2_id = fields.Many2one(comodel_name="res.users", string="Approver 2", domain=lambda self: self._get_approval2_domain())
    approver3_id = fields.Many2one(comodel_name="res.users", string="Approver 3", domain=lambda self: self._get_approval3_domain())
    approver4_id = fields.Many2one(comodel_name="res.users", string="Approver 4", domain=lambda self: self._get_approval4_domain())

    # def payment_approval_signed1_employee(self):
    #     return self.env['hr.employee'].sudo().search([('user_id', '=', self.payment_approval_signed1_id.id)])
    #
    # def payment_approval_signed2_employee(self):
    #     return self.env['hr.employee'].sudo().search([('user_id', '=', self.payment_approval_signed2_id.id)])

    def _get_approval1_domain(self):
        return [("id", "in", self.env.ref("bill_of_quantity_approval.group_boq_approval1").users.ids)]

    def _get_approval2_domain(self):
        return [("id", "in", self.env.ref("bill_of_quantity_approval.group_boq_approval2").users.ids)]

    def _get_approval3_domain(self):
        return [("id", "in", self.env.ref("bill_of_quantity_approval.group_boq_approval3").users.ids)]

    def _get_approval4_domain(self):
        return [("id", "in", self.env.ref("bill_of_quantity_approval.group_boq_approval4").users.ids)]

    def _set_default_approval(self):
        self.ensure_one()
        if not self.approver1_id:
            self.approver1_id = self.env.ref("bill_of_quantity_approval.group_boq_approval1").users[0].id if len(self.env.ref("bill_of_quantity_approval.group_boq_approval1").users) else False
        if not self.approver2_id:
            self.approver2_id = self.env.ref("bill_of_quantity_approval.group_boq_approval2").users[0].id if len(self.env.ref("bill_of_quantity_approval.group_boq_approval2").users) else False
        if not self.approver3_id:
            self.approver3_id = self.env.ref("bill_of_quantity_approval.group_boq_approval3").users[0].id if len(self.env.ref("bill_of_quantity_approval.group_boq_approval3").users) else False
        if not self.approver4_id:
            self.approver4_id = self.env.ref("bill_of_quantity_approval.group_boq_approval4").users[0].id if len(self.env.ref("bill_of_quantity_approval.group_boq_approval4").users) else False

    @api.model
    def create(self, vals):
        res = super(Bill_Quantity, self).create(vals)
        res._set_default_approval()
        return res

    # def write(self, vals):
    #     amount_total = self.amount_total
    #     res = super(SaleOrder, self).write(vals)
    #     if self.amount_total != amount_total:
    #         self._set_default_approval()
    #     return res

    def get_approver_status(self, approver=False):
        if approver:
            return getattr(self, approver) in self.reviewer_ids
        else:
            return len(self.reviewer_ids.ids) > 0