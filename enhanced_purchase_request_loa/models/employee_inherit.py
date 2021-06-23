from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EmployeeInheritPRLoA(models.Model):
    _inherit = 'hr.employee'

    checkerPR = fields.Boolean(string='PR Checker')
    