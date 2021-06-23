# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class InventoryAdjustment(models.Model):
	_inherit = 'stock.inventory'

	force_date = fields.Datetime(string="Force Date")

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	force_date = fields.Datetime(string="Force Date")


class StockMove(models.Model):
	_inherit = 'stock.move'

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
							if move.inventory_id:
								account_move.write({'ref':move.inventory_id.name})

		return res
