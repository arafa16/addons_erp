# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Bank(models.Model):
    _inherit = 'res.bank'

    name = fields.Char(required=True)

    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for bank in self:
            name = bank.name #+ (bank.bic and (' - ' + bank.bic) or '')
            result.append((bank.id, name))
        return result


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    acc_name = fields.Char('Account Name')
