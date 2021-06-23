from odoo import models, fields, api, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

    bank_acc_holder_name = fields.Char(string='Holder Name')
    bank_name = fields.Char(string='Bank Name')
