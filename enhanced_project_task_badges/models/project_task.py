from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectTask(models.Model):
    _inherit = 'project.task'
    kanban_baru = fields.Selection(
        selection=[
            ('A', 'Not Started'),
            ('B', 'On Progress'),
            ('C', 'Stop Clock'),
            ('D', 'Done'),
            ('E', 'Cancel')
            ],
        string='Status Pelaksanaan',default='A')
    
    @api.multi
    def write(self, values):
        bb = values.get('stage_id',False)
        if bb == False:
            ww = 4
        else:
            if self.kanban_baru == 'D':
                values['kanban_baru'] = 'A'
            else:
                raise UserError('Stage dapat dipindahkan apabila status pelaksanaan sudah DONE')
                values = {}
        return super(ProjectTask, self).write(values)