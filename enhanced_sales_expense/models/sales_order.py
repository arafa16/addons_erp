from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    advance_sum = fields.Integer(string='Total Advance', compute='_get_advance_sum')
    advance_ids = fields.One2many('hr.advance', 'order_id', string='Cash Advance')
    expense_sum = fields.Integer(string='Total Expense', compute='_get_expense_sum')
    expense_ids = fields.One2many('hr.expense.sheet', 'order_id', string='Expense')

    def _get_advance_sum(self):
        for sale in self:
            sale.advance_sum = sum(self.advance_ids.filtered(lambda a: a.state not in ('cancel', 'reject')).mapped('total_amount_expense'))

    def _get_expense_sum(self):
        for sale in self:
            sale.expense_sum = sum(self.expense_ids.filtered(lambda a: a.state not in ('cancel')).mapped('expense_amount'))

    def action_view_cash_advance(self):
        if not any(self.advance_ids):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Request Cash Advance',
                'res_model': 'hr.advance',
                'view_type': 'form',
                # 'domain': [('task_id','=', self.id)],
                'context': {'default_order_id' : self.id, 'default_reason_for_advance': self.name},
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Request Cash Advance',
                'res_model': 'hr.advance',
                'view_type': 'form',
                'domain': [('order_id','=', self.id)],
                'context': {'default_order_id': self.id, 'default_reason_for_advance': self.name},
                'view_mode': 'tree,form',
                'target': 'current',
            }

    def action_expense_sheet(self):
        if not any(self.expense_ids):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Expense',
                'res_model': 'hr.expense.sheet',
                'view_type': 'form',
                # 'domain': [('task_id','=', self.id)],
                'context': {'default_order_id' : self.id, 'default_communication': self.name},
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Expense',
                'res_model': 'hr.expense.sheet',
                'view_type': 'form',
                'domain': [('order_id','=', self.id)],
                'context': {'default_order_id' : self.id, 'default_communication': self.name},
                'view_mode': 'tree,form',
                'target': 'current',
            }
