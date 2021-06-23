# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class Inventory_Inherit(models.Model):
    _inherit = "stock.inventory"

    is_cancel_inv = fields.Boolean('Is Cancelled')

    def cancel_stock_inventory(self):
        for move in self.move_ids :

            lot_id = False
            for lot in move.move_line_ids :
                lot_id = lot.lot_id
            if move.location_dest_id.usage == 'inventory' :
                if move.product_id.tracking == 'none':

                    quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id),('lot_id','=',lot_id.id)],limit=1)
                    quant._update_available_quantity(move.product_id,move.location_id,move.quantity_done)
                else :
                    quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_id.id)],limit=1)
                    quant._update_available_quantity(move.product_id,move.location_id,move.quantity_done,lot_id)
            else :
                if move.product_id.tracking == 'none':
                    quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_dest_id.id),('lot_id','=',lot_id.id)],limit=1)
                    quant._update_available_quantity(move.product_id,move.location_dest_id,-move.quantity_done)
                else :
                    quant = self.env['stock.quant'].search([('product_id','=',move.product_id.id),('location_id','=',move.location_dest_id.id)],limit=1)
                    
                    quant._update_available_quantity(move.product_id,move.location_dest_id,-move.quantity_done,lot_id)


            for line in move._get_move_lines():
                line.write({'state':'draft'})
            move.sudo()._action_cancel()
            self.write({'is_cancel_inv':True})
            journal_rec = self.env['account.move'].sudo().search([('stock_move_id','=',move.id)],order="id desc", limit=1)
            journal_rec.button_cancel()
            journal_rec.sudo().unlink()
            move.sudo().unlink()

        self.write({'state':'cancel'})
        return

    def action_cancel_draft(self):
        self.mapped('move_ids')._action_cancel()
        if self.is_cancel_inv:
            self.write({'state': 'draft'})
        else:
            self.write({'line_ids': [(5,)],'state': 'draft'})


class stock_move_line(models.Model):
    _inherit= "stock.move.line"

    def unlink(self):
        #custom code
        if self:
            if self[0].move_id.inventory_id :
                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                for ml in self:
                    # Unlinking a move line should unreserve.
                    if ml.product_id.type == 'product' and not ml.location_id.should_bypass_reservation() and not float_is_zero(ml.product_qty, precision_digits=precision):
                        try:
                            self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                        except UserError:
                            if ml.lot_id:
                                self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                            else:
                                raise
                moves = self.mapped('move_id')
                if moves:
                    moves._recompute_state()
                res = super(stock_move_line, self).unlink()
                return res

            #custom code
            else :
                res = super(stock_move_line, self).unlink()
                return res


class stock_move_inherit(models.Model):
    _inherit = "stock.move"

    def _action_cancel(self):
        #custom code
        if self.inventory_id :
            for move in self:
                if move.state == 'cancel':
                    continue
                move._do_unreserve()
                siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
                if move.propagate:
                    # only cancel the next move if all my siblings are also cancelled
                    if all(state == 'cancel' for state in siblings_states):
                        move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
                else:
                    if all(state in ('done', 'cancel') for state in siblings_states):
                        move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                        move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
            self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
            return True
        #custom code
        else :
            if any(move.state == 'done' for move in self):
                raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))
            for move in self:
                if move.state == 'cancel':
                    continue
                move._do_unreserve()
                siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
                if move.propagate:
                    # only cancel the next move if all my siblings are also cancelled
                    if all(state == 'cancel' for state in siblings_states):
                        move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
                else:
                    if all(state in ('done', 'cancel') for state in siblings_states):
                        move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                        move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
            self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
            return True

    def _do_unreserve(self):
        #custom code
        for rec in self:
            if rec.inventory_id :
                moves_to_unreserve = self.env['stock.move']
                for move in self:
                    if move.state == 'cancel':
                        # We may have cancelled move in an open picking in a "propagate_cancel" scenario.
                        continue
                    if move.state == 'done':
                        if move.scrapped:
                            # We may have done move in an open picking in a scrap scenario.
                            continue
                        else:
                            pass
                            #raise UserError(_('You cannot unreserve a stock move that has been set to \'Done\'.'))
                    moves_to_unreserve |= move
                moves_to_unreserve.mapped('move_line_ids').unlink()
                return True
            #custom code
            else :
                moves_to_unreserve = self.env['stock.move']
                for move in self:
                    if move.state == 'cancel':
                        # We may have cancelled move in an open picking in a "propagate_cancel" scenario.
                        continue
                    if move.state == 'done':
                        if move.scrapped:
                            # We may have done move in an open picking in a scrap scenario.
                            continue
                        else:
                            raise UserError(_('You cannot unreserve a stock move that has been set to \'Done\'.'))
                    moves_to_unreserve |= move
                moves_to_unreserve.mapped('move_line_ids').unlink()
                return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

