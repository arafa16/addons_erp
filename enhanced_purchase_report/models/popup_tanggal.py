from odoo import fields, models, api, _
from odoo.exceptions import UserError
import base64
import xlwt
import pytz
from io import BytesIO
from pprint import pprint
from datetime import datetime
import math

class PurchaseorderlineReportAll(models.TransientModel):
    _name = 'enhanced.wizard.purchasereport'

    tanggal_awal = fields.Datetime(string='Start date')
    tanggal_ahir = fields.Datetime(string='End date')

    excel_file = fields.Binary(string='Download Report Excel', readonly="1")
    
    @api.multi
    def process_wizard(self):
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet('CLOSE',cell_overwrite_ok=True)
        style1 = xlwt.easyxf('font: bold True, color black; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color gray40; align: horiz center;')
        style2 = xlwt.easyxf('font: bold off, color black; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color white;')
        style3 = xlwt.easyxf('font: bold off, color black; align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color white;')
        style4 = xlwt.easyxf('font: bold off, color black; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color white;',"#,###")
        worksheet.write(0,0,'No',style1)
        worksheet.write(0,1,'No PR',style1)
        worksheet.write(0,2,'HARGA / PRODUCT',style1)
        worksheet.write(0,3,'TGL PROCURE RECEIVE',style1)
        worksheet.write(0,4,'NO PO',style1)
        worksheet.write(0,5,'TGL PO',style1)
        worksheet.write(0,6,'RESPONSIBLE',style1)
        worksheet.write(0,7,'NOMOR SO',style1)
        worksheet.write(0,8,'NILAI SO',style1)
        worksheet.write(0,9,'VENDOR',style1)
        worksheet.write(0,10,'DESCRIPTION PRODUCT',style1)
        worksheet.write(0,11,'HARGA SATUAN',style1)
        worksheet.write(0,12,'JUMLAH BARANG',style1)
        worksheet.write(0,13,'TOTAL NILAI PO/PUM',style1)
        worksheet.write(0,14,'SCHEDULE DATE',style1)
        worksheet.write(0,15,'END DATE',style1)
        worksheet.write(0,16,'PRODUCT CATEGORY',style1)
        worksheet.write(0,17,'PAYMENT TERM',style1)
        worksheet.write(0,18,'COA',style1)
        worksheet.write(0,19,'REQUEST BY',style1)
        worksheet.write(0,20,'STATUS GRN',style1)
        worksheet.write(0,21,'TGL VALIDATE DO',style1)
        produkline = self.env['purchase.order.line'].search(['&','&',('order_id.state','in',['requestloa','loaconfirmed','to approve','purchase','done']),
                                                             ('order_id.requisition_id.nomor_pr.tanggal_procure','>=',self.tanggal_awal),
                                                             ('order_id.requisition_id.nomor_pr.tanggal_procure','<=',self.tanggal_ahir)])
        baris = 1
        for produk in produkline:
            prnya = produk.order_id.requisition_id.nomor_pr
            prline = self.env['sprogroup.purchase.request.line'].sudo().search([('request_id', '=', prnya.id), ('product_id', '=', produk.product_id.id)], limit=1)
            worksheet.write(baris,0,'',style2)
            worksheet.write(baris,1,prnya.name,style2)
            worksheet.write(baris,2,prline.subtotal,style4)
            worksheet.write(baris,3,prnya.tanggal_procure,style2)
            worksheet.write(baris,4,produk.order_id.name,style2)
            worksheet.write(baris,5,produk.order_id.date_order,style2)
            worksheet.write(baris,6,produk.order_id.requisition_id.user_id.name,style2)
            worksheet.write(baris,7,prnya.salesorder_id.name,style2)
            worksheet.write(baris,8,prnya.salesorder_id.amount_total,style4)
            worksheet.write(baris,9,produk.order_id.partner_id.name,style2)
            worksheet.write(baris,10,produk.name,style2)
            worksheet.write(baris,11,produk.price_unit,style4)
            worksheet.write(baris,12,produk.product_qty,style2)
            worksheet.write(baris,13,produk.price_subtotal,style4)
            worksheet.write(baris,14,produk.date_planned,style2)
            worksheet.write(baris,15,produk.order_id.date_planned,style2)
            worksheet.write(baris,16,produk.product_id.categ_id.name,style2)
            worksheet.write(baris,17,produk.order_id.payment_term_id.name,style2)
            worksheet.write(baris,18,produk.product_id.categ_id.property_stock_account_input_categ_id.name,style2)
            worksheet.write(baris,19,produk.order_id.requisition_id.nomor_pr.requested_by.name,style2)
            if len(produk.move_ids) > 0:
                fill18 = produk.move_ids[0].state
                fill19 = produk.move_ids[0].date
            else:
                fill18 = ''
                fill19 = ''
            worksheet.write(baris,20,fill18,style2)
            worksheet.write(baris,21,fill19,style2)
            baris = baris + 1
        fp = BytesIO()
        workbook.save(fp)
        self.excel_file = base64.encodestring(fp.getvalue())
        fp.close()
        return {
            'type' : 'ir.actions.act_url',
            'url' : 'web/content/?model=enhanced.wizard.purchasereport&field=excel_file&download=true&id=%s&filename=Report.xls'%(self.id),
            'target' : 'new'
        }