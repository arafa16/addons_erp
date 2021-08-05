from odoo import models, fields, api, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    show_tax_report = fields.Boolean(string='Tax Report', index=True, default=False)
