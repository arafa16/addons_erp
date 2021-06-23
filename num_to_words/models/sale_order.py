# -*- coding: utf-8 -*-

from num2words import num2words
from odoo import api, fields, models, _
import re
import math

class SaleOrderExtended(models.Model):
    _inherit = "sale.order"

    text_amount = fields.Char(string="Terbilang", required=False, compute="amount_to_words" )

    def titlecase(self, s):
        return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
            lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(), s)
    
    @api.depends('amount_total')
    def amount_to_words(self):
        if self.company_id.text_amount_language_currency:
#            self.text_amount = num2words(self.amount_total, to='currency',
#                lang=self.company_id.text_amount_language_currency)
            i_amount_total = int(self.amount_total)
            if (float(i_amount_total) < self.amount_total) :
                self.text_amount = self.titlecase(num2words(self.amount_total, to='currency',
                    lang=self.company_id.text_amount_language_currency))
            elif (float(i_amount_total) == self.amount_total) :
                self.text_amount = self.titlecase(num2words(i_amount_total, to='currency',
                    lang=self.company_id.text_amount_language_currency))


