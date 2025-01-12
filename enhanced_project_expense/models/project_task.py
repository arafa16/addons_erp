from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # purchase_req = fields.Many2one('sprogroup.purchase.request', string='Purchase Request')
    advance_ids = fields.One2many('hr.advance', 'task_id', string='Cash Advance')
    sheet_ids = fields.One2many('hr.expense.sheet', 'task_id', string='Expense')

    # @api.multi
    def action_request_cash_advance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Cash Advance',
            'res_model': 'hr.advance',
            'view_type': 'form',
            # 'domain': [('task_id','=', self.id)],
            'context': {'default_task_id' : self.id, 'default_order_id' : self.sale_order_id.id, 'default_reason_for_advance': self.name},
            'view_mode': 'form',
            'target': 'current',
        }

    def action_expense_sheet(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense',
            'res_model': 'hr.expense.sheet',
            'view_type': 'form',
            # 'domain': [('task_id','=', self.id)],
            'context': {'default_task_id' : self.id, 'default_order_id' : self.sale_order_id.id, 'default_communication': self.name},
            'view_mode': 'form',
            'target': 'current',
        }
