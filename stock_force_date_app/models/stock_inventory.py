# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class InventoryAdjustment(models.Model):
	_inherit = 'stock.inventory'

	force_date = fields.Datetime(string="Force Date")

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	force_date = fields.Datetime(string="Force Date")


class StockMove(models.Model):
	_inherit = 'stock.move'

	@api.multi
	def _check_lock_date(self, move):
		if move:
			lock_date = max(move.company_id.period_lock_date or '0000-00-00',
							move.company_id.fiscalyear_lock_date or '0000-00-00')
			if self.user_has_groups('account.group_account_manager'):
				lock_date = move.company_id.fiscalyear_lock_date
			if move.date <= (lock_date or '0000-00-00'):
				if self.user_has_groups('account.group_account_manager'):
					message = _("You cannot add/modify entries prior to and inclusive of the lock date %s") % (
						lock_date)
				else:
					message = _(
						"You cannot add/modify entries prior to and inclusive of the lock date %s. Check the company settings or ask someone with the 'Adviser' role") % (
								  lock_date)
				raise UserError(message)
		return True

	def _action_done(self):
		force_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
			for move in self:
				if move.picking_id:
					if move.picking_id.force_date:
						force_date = move.picking_id.force_date
					else:
						force_date = move.picking_id.scheduled_date

				if move.inventory_id:
					if move.inventory_id.force_date:
						force_date = move.inventory_id.force_date
					else:
						force_date = move.inventory_id.date

		# Check CC and AA
		for move in self:
			employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)])
			if employee:
				if not move.cost_center_id:
					move.cost_center_id = employee.cost_center_id.id
				if not move.analytic_account_id:
					move.analytic_account_id = employee.analytic_account_id.id

		res = super(StockMove, self)._action_done()
		if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
			if force_date:
				for move in res:
					move.write({'date':force_date})
					if move.move_line_ids:
						for move_line in move.move_line_ids:
							move_line.write({'date':force_date})
					if move.account_move_ids:
						for account_move in move.account_move_ids:
							account_move.write({'date':force_date})
							self._check_lock_date(account_move)
							if move.inventory_id:
								account_move.write({'ref':move.inventory_id.name})
		return res
