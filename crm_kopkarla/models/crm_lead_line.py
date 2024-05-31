from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import float_is_zero


class bill_quantity_line(models.Model):
    _name = 'crm.lead.line'
    _description = 'CRM Line'

    crm_id = fields.Many2one('crm.lead', 'CRM', ondelete='cascade')
    product = fields.Char(string='Product')
    product_brand = fields.Char('Brand')
    product_type = fields.Char('Type')
    name = fields.Text('Description')
    lokasi_kirim = fields.Char('Lokasi Kirim')

    expired_date = fields.Date('Expired Date')
    # delivery = fields.Char('Delivery Time')
    franco = fields.Char('Franco')
    # payment_term_id = fields.Many2one('account.payment.term', 'Payment Term')

    garansi = fields.Char('Garansi')
    uom_id = fields.Many2one('product.uom', 'Unit of Measure',)
    qty = fields.Float("Qty", default=1)
    # price_unit = fields.Float("Cost", default = 0.0,)
    # price_service = fields.Float("Cost Service", default = 0.0,)
    # price_subtotal = fields.Float("Subtotal", compute='_compute_price', default = 0.0, readonly=True, store=True,)
    # service_subtotal = fields.Float("Subtotal Service", compute='_compute_price', default = 0.0, readonly=True, store=True,)
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('done', 'Done'),
    #     ('reject', 'Rejected'),
    #     ('cancel', 'Canceled'),
    # ], string='Status', default='draft')

    # @api.depends('price_unit', 'price_service', 'sale_price', 'sale_service', 'qty', 'product_id')
    # def _compute_price(self):
    #     for i in self:
    #         i.price_subtotal = i.qty * i.price_unit
    #         i.service_subtotal = i.qty * i.price_service
    #         i.sale_subtotal = i.qty * i.sale_price
    #         i.sale_service_subtotal = i.qty * i.sale_service
    #         i.revenue_margin = (((i.sale_subtotal + i.sale_service_subtotal) - (i.price_subtotal + i.service_subtotal)) / (i.sale_subtotal + i.sale_service_subtotal) * 100) if (i.sale_subtotal + i.sale_service_subtotal) != 0 else 0
