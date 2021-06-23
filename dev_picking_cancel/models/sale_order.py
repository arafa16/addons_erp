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


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def unlink(self):
        for sale in self:
            if sale.picking_ids:
                raise ValidationError(
                    _('Plase Unlink all picking of this sale order'))
            if sale.invoice_ids:
                raise ValidationError(
                    _('Plase Unlink all Invoice of this sale order'))
        return super(sale_order, self).unlink()

    @api.multi
    def action_cancel(self):
        if self.picking_ids:
            for picking in self.picking_ids:
                if picking.state != 'cancel':
                    picking.action_cancel()

        if self.invoice_ids:
            for invoice in self.invoice_ids:
                if invoice.state != 'cancel':
                    invoice.action_invoice_cancel()
                    invoice.move_name = False
        return self.write({'state': 'cancel'})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
