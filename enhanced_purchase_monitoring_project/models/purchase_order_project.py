from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrderProject(models.Model):
    _inherit = 'purchase.order'

    gettask_rel = fields.Many2one('project.task', string='Project Rel', related="requisition_id.nomor_pr.pjtask", store=True,)
    getstage_rel = fields.Many2one('project.task.type', string='Project Task Rel', related="gettask_rel.stage_id", store=True,)
    ww = 4