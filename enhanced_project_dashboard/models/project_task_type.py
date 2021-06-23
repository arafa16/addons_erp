from odoo import models, fields, api, _
from odoo.exceptions import UserError

class projectDashboardProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    ww = 4