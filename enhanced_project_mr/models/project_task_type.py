from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    material_req = fields.Boolean(
        help="apabila di cheklist maka"
             " Diperbolehkan untuk melakukan MR",
        string="Material Request"
    )
    material_ret = fields.Boolean(
        help="apabila di cheklist maka"
             " Diperbolehkan untuk melakukan Return Material",
        string="Material Return"
    )
    ready_invoice = fields.Boolean(
        help="apabila di cheklist maka"
             " State Ready to Invoice",
        string="Invoiceable"
    )
