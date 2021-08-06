from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    note = fields.Text('Terms and conditions', compute='_get_sales_attribute')
    penandatangan  = fields.Many2one('hr.employee', compute='_get_sales_attribute')
    pegawai_ttd = fields.Many2one('hr.employee', compute='_get_sales_attribute')

    @api.multi
    @api.depends('code')
    def _get_sales_attribute(self):
        for analytic in self:
            sale = self.env['sale.order'].sudo().search([('name','=',analytic.code)], limit=1)
            analytic.note = sale.note
            analytic.pegawai_ttd = sale.pegawai_ttd
            if sale.required5 == True:
                analytic.penandatangan = sale.penandatangan5.id
            elif sale.required4 == True:
                analytic.penandatangan = sale.penandatangan4.id
            elif sale.required3 == True:
                analytic.penandatangan = sale.penandatangan3.id
            elif sale.required2 == True:
                analytic.penandatangan = sale.penandatangan2.id
            else:
                analytic.penandatangan = sale.penandatangan1.id
