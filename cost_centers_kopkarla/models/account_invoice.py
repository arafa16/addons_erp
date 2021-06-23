# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # cost_center_id = fields.Many2one("cost.center", string='Cost Center')

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        if line.get('cost_center_id'):
            res['cost_center_id'] = line['cost_center_id']
        if line.get('account_analytic_id'):
            res['analytic_account_id'] = line['account_analytic_id']
        return res

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()

        for dict_data in res:
            invl_id = dict_data.get('invl_id')
            line = self.env['account.invoice.line'].browse(invl_id)
            if line.cost_center_id:
                dict_data['cost_center_id'] = line.cost_center_id.id

        return res

    # @api.onchange('cost_center_id')
    # def _onchange_cost_center_id(self):
    #     if self.cost_center_id:
    #         for line in self.invoice_line_ids:
    #             line.cost_center_id = self.cost_center_id

    @api.model
    def default_get(self,fields):
        result = super(AccountInvoice, self).default_get(fields)
        if result.get('purchase_id'):
            po_id = result.get('purchase_id')
            purchase_order = self.env['purchase.order'].browse(po_id)
            # result.update({'cost_center_id': purchase_order.cost_center_id and purchase_order.cost_center_id.id or False})
        return result

    # @api.onchange('cost_center_id')
    # def set_cost_center(self):
    #     for line in self.invoice_line_ids:
    #         line.cost_center_id = self.cost_center_id.id

class AccountInvoiceLine(models.Model):

    _inherit='account.invoice.line'

    cost_center_id = fields.Many2one("cost.center", string="Cost Center",)

    purchase_line_id = fields.Many2one('purchase.order.line', 'Purchase Order Line', ondelete='set null', index=True)

    # @api.onchange('quantity')
    # def set_default_cost_center(self):
    #     if self.invoice_id.cost_center_id:
    #         self.cost_center_id = self.invoice_id.cost_center_id.id
