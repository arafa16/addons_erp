from odoo import models, fields, api

class EnhancedSalesArea(models.Model):
    _name = 'enhanced.sales.area'
    _order = 'urutan asc'
    name = fields.Char(string='Sales Area')
    description = fields.Char(string='Description')
    urutan = fields.Integer(string='Sequence')

    def fungsi_sementara(self):
        getso = self.env['sale.order'].search([('jenis_so','=','Project')])
        for so in getso:
            setsing = ''
            if so.partner_id.singkatan != '':
                setsing = so.partner_id.singkatan
            if so.partner_invoice_id.singkatan != '':
                setsing = so.partner_shipping_id.singkatan
            if setsing != '':
                getmasterarea = self.env['enhanced.sales.area'].search([('name','=',setsing)])
                if getmasterarea.id != False:
                    so.write({'sales_area':getmasterarea.id})