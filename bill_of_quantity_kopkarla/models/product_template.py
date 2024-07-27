from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand = fields.Char('Brand')
    product_type = fields.Char('Type')
