from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


class BudgetRequest(models.Model):
    _inherit = "budget.request"

    tier_validate = fields.Boolean(string='Tier Validation', default=False)

    def _budget_request_approve_action(self):
        msg = ''
        is_approved = True
        if self.env.context.get('force') == 0 or not self.allow_unbudget:
            for req in self.line_ids:
                if req.restrict_allow != 'allow':
                    if req.requested_amount > req.available_running_budget: # req.available_budget:
                        msg = (req.selected_budget_id and 'Requested amount Rp %s,- lebih besar dari available budget Rp %s,-.\n' % ('{:,.0f}'.format(req.requested_amount), '{:,.0f}'.format(req.available_running_budget))) or \
                              '%sAccount %s has no budget selected.\n' % (msg, req.budget_account_id.name)
                        if req.restrict_allow == 'restrict' or not req.selected_budget_id:
                            is_approved = False
        if is_approved:
            self.date = datetime.now()
            self.state = 'done'
            if self.origin == 'purchase_request':
                self.request_id.budget_request_id = self.id
                self.request_id.request_budget_approval()
            elif self.origin == 'expense_request':
                if not any(self.sheet_id.reviewer_ids):
                    self.sheet_id.state = 'approve'
                elif not self.tier_validate:
                    self.sheet_id.validate_tier()
                    self.tier_validate = True
            if msg:
                view = self.env.ref('sh_message.sh_message_wizard')
                view_id = view and view.id or False
                return {
                    'name': 'Warning: Budget approved',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': {'message': msg},
                }
        else:
            msg = '%s\nBudget requested tidak di approved.' % msg
            raise UserError(msg)
