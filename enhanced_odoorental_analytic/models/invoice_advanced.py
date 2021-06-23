from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime

class InheritInvoicedAdvanced(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def create_invoices(self):
        pay_method = self.advance_payment_method
        so_id = self._context.get('active_id',False)
        so_doc = self.env['sale.order'].browse(so_id)
        if (pay_method == 'delivered' or pay_method == 'all') and so_doc.is_rental_so == True:
            # buat dokumen analytic account
            dd = datetime.datetime.today()
            line_order = so_doc.order_line
            maxtenur = 0
            namakategori = ''
            prodquant = 0
            hargaperbulan = 0
            namaproduk = ''
            for baris in line_order:
                if baris.rental_tenure > maxtenur:
                    maxtenur = baris.rental_tenure
                namakategori = baris.product_id.categ_id.name
                prodquant = baris.product_uom_qty
                hargaperbulan = baris.price_total / baris.rental_tenure / baris.product_uom_qty
                namaproduk = baris.name
            namakategori = 'Sewa ' + namakategori
            habis = False
            ii = 0
            tanggal = dd.day
            bulan = dd.month
            tahun = dd.year
            while habis == False:
                if ii > 1:
                    bulan = bulan + 1
                    if bulan > 12:
                        bulan = 1
                        tahun = tahun + 1
                ii = ii + 1
                if ii > maxtenur:
                    habis = True
            if bulan < 10:
                bulannama = '0'+str(bulan)
            else:
                bulannama = str(bulan)
            if tanggal < 10:
                tglnama = '0'+str(tanggal)
            else:
                tglnama = str(tanggal)

            tglakhir = str(tahun)+'-'+bulannama+'-'+tglnama

            jurnal = self.env['account.journal'].search([('type','=','sale'),('company_id','=',so_doc.company_id.id)])
            jurnalid = False
            if len(jurnal) > 0:
                jurnalid = jurnal[0].id

            isi = {}
            isi['active'] = True
            isi['code'] = so_doc.name
            isi['company_id'] = so_doc.company_id.id
            isi['contract_template_id'] = False
            isi['contract_type'] = 'sale'
            isi['date_end'] = tglakhir
            isi['date_start'] = dd.strftime('%Y-%m-%d')
            isi['journal_id'] = jurnalid
            isi['name'] = str(namakategori)+', '+str(so_doc.partner_shipping_id.name)
            isi['parent_id'] = so_doc.analytic_account_id.id
            isi['partner_id'] = so_doc.partner_id.id
            isi['pricelist_id'] = so_doc.pricelist_id.id
            isi['recurring_interval'] = 1
            isi['recurring_invoices'] = True
            isi['recurring_invoicing_type'] = 'pre-paid'
            isi['recurring_next_date'] = dd.strftime('%Y-%m-%d')
            isi['recurring_rule_type'] = 'monthly'
            isi['sale_order_id'] = so_doc.id
            tagid = []
            tagidisi = []
            tagidisi.append(6)
            tagidisi.append(False)
            kodetagid = []
            tagidisi.append(kodetagid)
            tagid.append(tagidisi)
            isi['tag_ids'] = tagid
            # prodrent = self.env['product.product'].search([('to_analytic','=',True)])
            # if len(prodrent) > 0:
            rec_ids = []
            for barisorder in line_order:
                rec_line = []
                rec_line.append(0)
                rec_line.append('virtual_20'+str(barisorder.id))
                rec_line_data = {}
                rec_line_data['automatic_price'] = False
                rec_line_data['discount'] = 0
                rec_line_data['name'] = barisorder.name
                rec_line_data['price_unit'] = barisorder.price_unit / barisorder.rental_tenure
                # rec_line_data['product_id'] = prodrent[0].id
                rec_line_data['product_id'] = barisorder.product_id.id
                rec_line_data['quantity'] = barisorder.product_uom_qty
                rec_line_data['sequence'] = 10
                rec_line_data['specific_price'] = barisorder.price_unit / barisorder.rental_tenure 
                # rec_line_data['uom_id'] = prodrent[0].uom_id.id
                rec_line_data['uom_id'] = barisorder.product_id.uom_id.id
                # rec_line_data['analytic_account_id'] = so_doc.analytic_account_id.id
                rec_line.append(rec_line_data)
                rec_ids.append(rec_line)
            isi['recurring_invoice_line_ids'] = rec_ids

            sale = self.env['sale.order'].sudo().search([('id', '=', so_doc.id)])
            sale.update({'invoice_status': 'invoiced'})
            for line in self.env['sale.order.line'].sudo().search([('order_id', '=', so_doc.id)]):
                line.update({'invoice_status': 'invoiced'})

            return self.env['account.analytic.account'].create(isi)

        return super(InheritInvoicedAdvanced,self).create_invoices()