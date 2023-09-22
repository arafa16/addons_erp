from odoo import models, fields, api, _
from odoo.exceptions import Warning,UserError
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import *

class AccountMove(models.Model):
    _inherit = "account.move"

    journal_prepair_by = fields.Many2one('hr.employee', string='Prepared By', default=lambda self: self.env['res.config.settings'].get_values().get('default_journal_prepair_by'))
    journal_approve_by = fields.Many2one('hr.employee', string='Approved By', default=lambda self: self.env['res.config.settings'].get_values().get('default_journal_approve_by'))
