from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    warehouse_ok = fields.Boolean('Warehouse Maintained', default=False)
