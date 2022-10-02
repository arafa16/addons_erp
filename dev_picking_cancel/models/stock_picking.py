# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_round, float_is_zero
import random


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_cancel(self):
        if self.picking_type_id.code == 'internal':
            if self.state == 'done' or 'confirmed':
                for move in self.move_lines:
                    pack_op = self.env['stock.move'].sudo().search(
                            [('picking_id', '=', move.picking_id.id), ('product_id', '=', move.product_id.id)])
                    move.set_quant_quantity(move, pack_op, move.picking_id.state)
                    
        res = super(stock_picking, self).action_cancel()
        account_pool = self.env['account.move']
        move_ids = account_pool.search([('ref', '=', self.name), ('state', '=', 'posted')])
        if move_ids:
            move_ids.sudo().button_cancel()
            move_ids.sudo().unlink()
                        
                        

    @api.multi
    def action_set_draft(self):
        move_obj = self.env['stock.move']
        for pick in self:
            ids2 = [move.id for move in pick.move_lines]
            moves = move_obj.browse(ids2)
            moves.sudo().action_draft()
            for move in moves:
                for m_line in move.move_line_ids:
                    m_line.unlink()
        return True


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def unlink_serial_number(self):
        if self.picking_type_id and self.picking_type_id.code == 'incoming':
            for line in self.move_line_ids:
                if line.lot_id:
                    line.lot_id.name = line.lot_id.name + '- Cancel - '+ str(random.randint(0,99999))
                    
                    
    @api.multi
    def action_draft(self):
        res = self.write({'state': 'draft'})
        return res

    def _do_unreserve(self):
        moves_to_unreserve = self.env['stock.move']
        for move in self:
            if move.state == 'cancel':
                # We may have cancelled move in an open picking in a "propagate_cancel" scenario.
                continue
            if move.state == 'done':
                if move.scrapped:
                    # We may have done move in an open picking in a scrap scenario.
                    continue
                for line in move.move_line_ids:
                    line.state = 'draft'

            moves_to_unreserve |= move
        moves_to_unreserve.mapped('move_line_ids').unlink()
        return True

    @api.multi
    def dev_set_quantity(self, move_qty, stock_move):
        quant_pool = self.env['stock.quant']
        product = stock_move.product_id
        if stock_move.product_id.tracking == 'none':
            out_qaunt = quant_pool.sudo().search(
                [('product_id', '=', product.id), ('location_id', '=', stock_move.location_id.id)])
            if not out_qaunt:
                out_qaunt = quant_pool.create({
                    'product_id':product and product.id or False,
                    'location_id':stock_move.location_id and stock_move.location_id.id or False,
                    'quantity':0,
                    'product_uom_id':stock_move.product_uom and stock_move.product_uom.id or False,
                })
            if out_qaunt:
                out_qaunt[0].quantity = out_qaunt[0].quantity + move_qty
                if out_qaunt[0].quantity == 0:
                        out_qaunt[0].unlink()
                
            out_qaunt = quant_pool.sudo().search(
                [('product_id', '=', product.id), ('location_id', '=', stock_move.location_dest_id.id)])
            if not out_qaunt:
                out_qaunt = quant_pool.create({
                    'product_id':product and product.id or False,
                    'location_id':stock_move.location_id and stock_move.location_id.id or False,
                    'quantity':0,
                    'product_uom_id':stock_move.product_uom and stock_move.product_uom.id or False,
                })
            if out_qaunt:
                out_qaunt[0].quantity = out_qaunt[0].quantity - move_qty
                if out_qaunt[0].quantity == 0:
                        out_qaunt[0].unlink()
        else:
            for line in stock_move.move_line_ids:
                out_qaunt = quant_pool.sudo().search(
                    [('product_id', '=', product.id), ('location_id', '=', stock_move.location_id.id),('lot_id','=',line.lot_id.id)])
                if not out_qaunt:
                    out_qaunt = quant_pool.create({
                        'product_id':product and product.id or False,
                        'location_id':stock_move.location_id and stock_move.location_id.id or False,
                        'quantity':0,
                        'product_uom_id':stock_move.product_uom and stock_move.product_uom.id or False,
                        'lot_id':line.lot_id and line.lot_id.id or False,
                    })
                if out_qaunt:
                    out_qaunt[0].quantity = out_qaunt[0].quantity + line.qty_done
                    if out_qaunt[0].quantity == 0:
                        out_qaunt[0].unlink()
                    
                    
                out_qaunt = quant_pool.sudo().search(
                    [('product_id', '=', product.id), ('location_id', '=', stock_move.location_dest_id.id),('lot_id','=',line.lot_id.id)])
                if not out_qaunt:
                    out_qaunt = quant_pool.create({
                        'product_id':product and product.id or False,
                        'location_id':stock_move.location_id and stock_move.location_id.id or False,
                        'quantity':0,
                        'product_uom_id':stock_move.product_uom and stock_move.product_uom.id or False,
                        'lot_id':line.lot_id and line.lot_id.id or False,
                    })
                if out_qaunt:
                    out_qaunt[0].quantity = out_qaunt[0].quantity - line.qty_done
                    if out_qaunt[0].quantity == 0:
                        out_qaunt[0].unlink()
                    
    
    @api.multi
    def set_quant_quantity(self, stock_move, pack_operation_ids, pick_state):
        for pack_operation_id in pack_operation_ids:
            move_qty = stock_move.product_uom_qty
            
            if stock_move.quantity_done:
                move_qty = stock_move.quantity_done
            if move_qty and pick_state == 'done':
                if stock_move.sale_line_id:
                    if stock_move.sale_line_id.qty_delivered >=  move_qty:
                        stock_move.sale_line_id.qty_delivered = stock_move.sale_line_id.qty_delivered - move_qty
                    
                if stock_move.purchase_line_id:
                    if stock_move.purchase_line_id.qty_received >= move_qty:
                        stock_move.purchase_line_id.qty_received = stock_move.purchase_line_id.qty_received - move_qty
                        
                self.dev_set_quantity(move_qty, stock_move)
        return True

    @api.multi
    def _action_cancel(self):
        for move in self:
            pick_state = move.picking_id.state
            move._do_unreserve()
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
            if move.propagate:
                if all(state == 'cancel' for state in siblings_states):
                    move.move_dest_ids._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})

            if move.picking_id.state in ['done','confirmed'] and move.picking_id.picking_type_id.code in ['incoming','outgoing']:
                pack_op = self.env['stock.move'].sudo().search(
                    [('picking_id', '=', move.picking_id.id), ('product_id', '=', move.product_id.id)])
                self.set_quant_quantity(move, pack_op, pick_state)

            move.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
            move.unlink_serial_number()
        
        return True


class stock_move_line(models.Model):
    _inherit = "stock.move.line"

    def unlink(self):
#        uom_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
#        for move_line in self:
#            if move_line.product_id.type == 'product' and not move_line.location_id.should_bypass_reservation() and not float_is_zero(
#                    move_line.product_qty, precision_digits=uom_precision):
#                self.env['stock.quant']._update_reserved_quantity(move_line.product_id, move_line.location_id,
#                                                                  -move_line.product_qty, lot_id=move_line.lot_id,
#                                                                  package_id=move_line.package_id,
#                                                                  owner_id=move_line.owner_id, strict=True)
        return super(stock_move_line, self).unlink()

    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.constrains('product_id')
    def check_product_id(self):
        if any(elem.product_id.type not in ('product','consu') for elem in self):
            raise ValidationError(_('Quants cannot be created for consumables or services.'))
