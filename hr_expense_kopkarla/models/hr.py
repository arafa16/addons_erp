from odoo import api, fields, models


class Department(models.Model):
    _inherit = "hr.department"
    _rec_name = 'name'