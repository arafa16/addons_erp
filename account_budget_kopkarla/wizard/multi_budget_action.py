from odoo import models, api, _
from odoo.exceptions import UserError


class ConfirmBudget(models.TransientModel):
    _name = "confirm.budget"
    _description = "Confirm Budget"

    @api.multi
    def confirm_budgets(self):
        context = dict(self._context or {})
        budgets = self.env['crossovered.budget'].browse(context.get('active_ids'))
        budgets_to_action = self.env['crossovered.budget']
        for budget in budgets:
            if budget.state == 'draft':
                budgets_to_action += budget
        if not budgets_to_action:
            raise UserError(_('There is no budget in draft state to confirm.'))
        budgets_to_action.action_budget_confirm()
        return {'type': 'ir.actions.act_window_close'}


class ValidateBudget(models.TransientModel):
    _name = "validate.budget"
    _description = "Validate Budget"

    @api.multi
    def validate_budgets(self):
        context = dict(self._context or {})
        budgets = self.env['crossovered.budget'].browse(context.get('active_ids'))
        budgets_to_action = self.env['crossovered.budget']
        for budget in budgets:
            if budget.state == 'confirm':
                budgets_to_action += budget
        if not budgets_to_action:
            raise UserError(_('There is no budget in confirm state to validate.'))
        budgets_to_action.action_budget_validate()
        return {'type': 'ir.actions.act_window_close'}


class DoneBudget(models.TransientModel):
    _name = "done.budget"
    _description = "Done Budget"

    @api.multi
    def done_budgets(self):
        context = dict(self._context or {})
        budgets = self.env['crossovered.budget'].browse(context.get('active_ids'))
        budgets_to_action = self.env['crossovered.budget']
        for budget in budgets:
            if budget.state == 'validate':
                budgets_to_action += budget
        if not budgets_to_action:
            raise UserError(_('There is no budget in validate state to done.'))
        budgets_to_action.action_budget_done()
        return {'type': 'ir.actions.act_window_close'}


class CancelBudget(models.TransientModel):
    _name = "cancel.budget"
    _description = "Cancel Budget"

    @api.multi
    def cancel_budgets(self):
        context = dict(self._context or {})
        budgets = self.env['crossovered.budget'].browse(context.get('active_ids'))
        budgets_to_action = self.env['crossovered.budget']
        for budget in budgets:
            if budget.state != 'cancel':
                budgets_to_action += budget
        if not budgets_to_action:
            raise UserError(_('There is no budget to cancel.'))
        budgets_to_action.action_budget_cancel()
        return {'type': 'ir.actions.act_window_close'}


class DraftBudget(models.TransientModel):
    _name = "draft.budget"
    _description = "Draft Budget"

    @api.multi
    def draft_budgets(self):
        context = dict(self._context or {})
        budgets = self.env['crossovered.budget'].browse(context.get('active_ids'))
        budgets_to_action = self.env['crossovered.budget']
        for budget in budgets:
            if budget.state == 'cancel':
                budgets_to_action += budget
        if not budgets_to_action:
            raise UserError(_('There is no budget to set to draft.'))
        budgets_to_action.action_budget_draft()
        return {'type': 'ir.actions.act_window_close'}
