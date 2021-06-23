from odoo import api, fields, models, tools, _

class Currency(models.Model):
    _inherit = "res.currency"

    rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=(12, 19),
                        help='The rate of the currency to the currency of rate 1.')


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    rate = fields.Float(digits=(12, 19), default=1.0, help='The rate of the currency to the currency of rate 1')
