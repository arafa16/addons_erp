from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    kanban_baru = fields.Selection(tracking=True)
    date_laporan_done = fields.Datetime('Laporan Done')
    
    @api.multi
    def write(self, values):
        ret = super(ProjectTask, self).write(values)
        if 'stage_id' in values or 'kanban_baru' in values:
            self.update_laporan_done()
        return ret

    def update_laporan_done(self):
        for task_id in self:
            laporan_done = False
            if task_id.stage_id.name == 'Laporan' and task_id.kanban_baru == 'D':
                laporan_done = datetime.today()
            task_id.update({
                'date_laporan_done': laporan_done
            })
