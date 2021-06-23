# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class CostCenter(models.Model):
    _name = 'cost.center'
    _description = "Cost center modes"

    name = fields.Char("Title")
    code = fields.Char("Code")
    company_id = fields.Many2one('res.company', string='Company')

    @api.model
    @api.depends('name', 'code')
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        result = []

        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        csm = self.search(domain + args, limit=limit)

        for cost_center in csm:
            if cost_center.code and cost_center.name:
                name = str(cost_center.code) + ' ' + str(cost_center.name)
                result.append((cost_center.id, name))
        return result
