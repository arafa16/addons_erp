# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class work_package(models.Model):
    _name = 'work.package'
    _description = 'Work Packages'

    @api.depends('cost_header_ids.cost_of_header')
    def _compute_amount(self):
        total = 0.0
        for cost_header in self.cost_header_ids:
            total += cost_header.cost_of_header
        self.work_package_cost = total

    name = fields.Char("Work Package Name")
    uom_id = fields.Many2one('product.uom', string='Unit of Measure')
    key = fields.Selection(
        [
            # ('labor', 'Labor'),
            ('operational', 'Operational'),
            ('permit', 'Permit'),
        ], 'Key')
    work_package_cost = fields.Float(
        'Work Package Cost', compute='_compute_amount',
        readonly=True, store=True,)
        # digits='Account', )
    cost_header_ids = fields.Many2many(
        comodel_name='cost.header',
        relation='work_package_cost_header_rel',
        column1='work_package_id',
        column2='cost_header_id',
        string='Cost Header')

    # work_package_cost = fields.Float(readonly=False,)
    # company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company,
    #                              required=True, store=True, readonly=True)
    # currency_id = fields.Many2one(comodel_name="res.currency", string='Currency', related='company_id.currency_id',
    #                               required=True, store=True, readonly=False, tracking=True)
