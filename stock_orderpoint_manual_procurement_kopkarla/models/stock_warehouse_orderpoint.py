from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from datetime import datetime


class Orderpointbo(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    variant_id = fields.Many2one('product.attribute.value', string='Variant')
    qty_onhand = fields.Float(string='On Hand', digits=dp.get_precision('Product Unit of Measure'), compute="_get_qty_onhand", search="_search_qty_onhand") # related="product_id.qty_available")
    qty_request = fields.Float(string='Requested', digits=dp.get_precision('Product Unit of Measure'), compute="_get_qty_request")
    request_ids = fields.Many2many('sprogroup.purchase.request.line', string='Request Lines', compute='_get_qty_request')
    qty_bid = fields.Float(string='Bidding', digits=dp.get_precision('Product Unit of Measure'), compute="_get_qty_bid")
    bid_ids = fields.Many2many('purchase.requisition.line', string='Purchase Requesition', compute='_get_qty_bid')
    qty_ordered = fields.Float(string='Ordered', digits=dp.get_precision('Product Unit of Measure'), compute="_get_qty_po")
    order_ids = fields.Many2many('purchase.order.line', string='Order Lines', compute='_get_qty_po')
    qty_to_request = fields.Float(string='Qty To Request', digits=dp.get_precision('Product Unit of Measure'), compute="_get_product_minus") #, store=True)
    product_minus = fields.Boolean(string='Qty Minus', compute="_get_product_minus", store=True, default=False)

    @api.model
    def _search_qty_onhand(self, operator, value):
        swo_ids = self.search([])
        # Force prefetch
        swo_ids.mapped("qty_onhand")
        swo = []
        for row in swo_ids:
            quant_obj = self.env['stock.quant']
            qty_available = quant_obj._get_available_quantity(row.product_id, row.location_id)
            if operator == '<':
                if qty_available < row.product_min_qty:
                    swo.append(row.id)
            elif operator == '>=':
                if qty_available >= row.product_min_qty:
                    swo.append(row.id)
        return [('id', 'in', swo)]

    def _get_qty_onhand(self):
        for row in self:
            quant_obj = self.env['stock.quant']
            qty_available = quant_obj._get_available_quantity(row.product_id, row.location_id)
            row.qty_onhand = qty_available

    @api.model
    def create(self, vals):
        if 'product_tmpl_id' in vals and 'variant_id' in vals:
            product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', vals['product_tmpl_id']), ('attribute_value_ids', '=', vals['variant_id'])])
            vals['product_id'] = product_id.id
        return super(Orderpointbo, self).create(vals)

    @api.multi
    def _get_qty_request(self):
        for row in self:
            qty = 0
            request_lines = set()
            pr = self.env['sprogroup.purchase.request.line'].sudo().search([('product_id','=',row.product_id.id),('request_state','not in',['rejected']),('nomor_bidding','=',False)])
            for line in pr:
                request_lines.update(line.mapped('id'))
                qty = float(qty) + float(line.product_qty)
            row.qty_request = qty
            row.request_ids = self.env['sprogroup.purchase.request.line'].browse(list(request_lines)).sorted()

    @api.multi
    def _get_qty_bid(self):
        for row in self:
            qty = 0
            bid_lines = set()
            bid = self.env['purchase.requisition.line'].sudo().search([('product_id','=',row.product_id.id),('state','not in',['done','cancel'])])
            for line in bid:
                bid_lines.update(line.mapped('id'))
                qty = float(qty) + float(line.product_qty)
            row.qty_bid = qty
            row.bid_ids = self.env['purchase.requisition.line'].browse(list(bid_lines)).sorted()

    @api.multi
    def _get_qty_po(self):
        for row in self:
            qty = 0
            order_lines = set()
            po = self.env['purchase.order.line'].sudo().search([('product_id','=',row.product_id.id),('state','not in',['cancel'])])
            for line in po:
                qty = float(qty) + float(line.product_qty) - float(line.qty_received)
                if float(line.product_qty) > float(line.qty_received):
                    order_lines.update(line.mapped('id'))
            row.qty_ordered = qty
            row.order_ids = self.env['purchase.order.line'].browse(list(order_lines)).sorted()

    @api.multi
    @api.depends('product_id','qty_onhand', 'qty_request','qty_ordered','product_min_qty','product_max_qty')
    def _get_product_minus(self):
        for row in self:
            total_qty = 0
            total_qty = float(row.qty_onhand) + float(row.qty_request) + float(row.qty_ordered)
            row.qty_to_request = row.product_max_qty - total_qty if row.product_min_qty - total_qty > 0 else 0
            if total_qty < row.product_min_qty :
                row.product_minus = True
            else:
                row.product_minus = False

    @api.multi
    def send_notification_below_minimum_stock(self):
        template_id = self.env.ref('stock_kopkarla.inventory_stock_monitoring_id')
        if template_id:
            template_id.body_html = template_id.body_html.replace('${object.procure_recommended_date}', datetime.strptime(self.procure_recommended_date, '%Y-%m-%d').strftime('%d %B %Y'))
            template_id.send_mail(self.id, force_send=True)
