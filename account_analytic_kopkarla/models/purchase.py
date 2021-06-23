from odoo import models, fields, api, _

from odoo.exceptions import ValidationError

class purchase_order_inherit(models.Model):
    _inherit = "purchase.order"

    analytic_account_id = fields.Many2one('account.analytic.account',string="Analytic Account")

class PurchaseOrderLine_inherit(models.Model):
    _inherit = "purchase.order.line"

    # account_analytic_id = fields.Many2one('account.analytic.account',string="Analytic Account",related="order_id.analytic_account_id",store=True)
    account_analytic_id = fields.Many2one('account.analytic.account',string="Analytic Account")
