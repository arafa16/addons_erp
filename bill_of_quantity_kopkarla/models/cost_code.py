from odoo import models, fields, api, _
# import odoo.addons.decimal_precision as dp


class cost_code(models.Model):
    _name = 'cost.code'
    _description = 'Cost Code'
    _order = 'key, cost_header_id' #, number'

    # number = fields.Integer("Cost Number", required=True)
    name = fields.Char("Cost Name", required=True)
    key = fields.Selection(
        [
            ('operational', 'Operational'),
            ('permit', 'Permit'),
            ('mitra', 'Mitra'),
        ], 'Key', required=True)
    # description = fields.Char("Description", required=True)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float("Cost (Material)", required=True)
    price_service = fields.Float("Biaya Jasa")
    sale_unit = fields.Float("Sales (Material)")
    sale_service = fields.Float("Sales Jasa")
    # qty = fields.Float("Qty", default=1, required=True)
    # sub_total = fields.Float('Sub Total', compute='_calc_total')
    cost_header_id = fields.Many2one('cost.header', "Cost Category", required=True)
    area_id = fields.Many2one('enhanced.sales.area', string='Area', required=True)

    # @api.depends('qty', 'price_unit')
    # def _calc_total(self):
    #     for code in self:
    #         code.sub_total = code.qty * code.price_unit