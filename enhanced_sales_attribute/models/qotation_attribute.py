from odoo import models, fields, api, _
from odoo.exceptions import UserError

class QotationAttribute(models.Model):
    _inherit = 'sale.order'
    nomor_surat = fields.Char(string='Reference Number')
    nomor_fam = fields.Char(string='R.F.Q')
    delivery_doc  = fields.Date(string='Delivery Date')
    jenis_so = fields.Selection([("common","General Order"),("Project","Project"),("rental","Rental Order")], string='Order Type',required=True,default=lambda self: self._context.get('default_jenis','Project'))
    
    att_note = fields.Many2one('enhanced.note.tabel', string='Note Template')

    spk_sementara  = fields.Char(string='SPK User')
    nomor_spk  = fields.Char(string='NO. SPK')
    tgl_spk  = fields.Date(string='Tanggal SPK')
    stat_spk = fields.Boolean(string="Ada SPK", default=False, track_visibility='onchange')
    
    type_reva = fields.Selection(selection=[('FPP', 'FPP'),('PR', 'PR')],default="FPP")
    stat_reva = fields.Many2one('enhanced.reva.tabel', string='Document Status')

    tgl_rental_start  = fields.Date(string='Start Date')
    tgl_rental_warning  = fields.Date(string='Warning Date')
    tgl_rental_end  = fields.Date(string='End Date')
    sales_area = fields.Char(string='Sales Area Old', related="partner_id.singkatan", store=True,)

    @api.onchange('type_reva')
    def validate_form(self):
        self.stat_reva = False
        
    @api.onchange('att_note')
    def setNote(self):
        self.note = self.att_note.deskripsi

    @api.onchange('jenis_so')
    def get_price(self):
        getmenu1 = self.env.ref('sale.menu_sale_quotations').action.id
        getmenu2 = self.env.ref('sale.menu_sale_order').action.id
        getmenu3 = self.env.ref('odoo_sale_rental.rental_sales_submenu_1').action.id
        vv = self._context['params'].get('action',False)
        if vv == getmenu1 or vv == getmenu2:
            # menu kotation dan sale order
            if self.jenis_so == 'rental':
                self.jenis_so = 'common'
                raise UserError('Rental Order Gunakan Menu Rental')
        if vv == getmenu3:
            self.jenis_so = 'rental'