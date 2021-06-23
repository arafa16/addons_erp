from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedPurchaseRequsitionRoutingList(models.Model):
    _inherit = 'purchase.requisition'

    def listVendorbarang(self):
        self.ensure_one()
        hasil = []
        for baris in self.line_ids:
            rowx = {}
            rowx['product_id'] = baris.product_id.name
            rowx['product_qty'] = baris.product_qty
            rowx['product_uom_id'] = baris.product_uom_id.name
            rowx['price_unit'] = baris.price_unit
            rowx['currency_id'] = self.company_id.currency_id
            rowx['schedule_date'] = baris.schedule_date
            # ini untuk vendor
            vendorx = []
            getpoline = self.env['purchase.order.line'].search(['&',('order_id.requisition_id','=',self.id),('product_id','=',baris.product_id.id)])
            for poline in getpoline:
                rowy = {}
                if poline.order_id.partner_id.parent_id.id != False:
                    rowy['vendor'] = poline.order_id.partner_id.parent_id.name + ', '+ poline.order_id.partner_id.name
                else:
                    rowy['vendor'] = poline.order_id.partner_id.name
                rowy['reference'] = poline.order_id.name
                rowy['vendor_date'] = poline.date_planned
                rowy['product_qty'] = poline.product_qty
                rowy['price_unit'] = poline.price_unit
                rowy['stat'] = poline.order_id.state
                vendorx.append(rowy)
            rowx['vendor'] = vendorx
            # end untuk vendor
            hasil.append(rowx)
        return hasil

    ww = 4