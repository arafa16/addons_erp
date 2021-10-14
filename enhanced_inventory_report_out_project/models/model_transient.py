from odoo import fields, models, api, _
from odoo.exceptions import UserError
import base64
import xlwt
import pytz
from io import BytesIO
from pprint import pprint
from datetime import datetime

class InventoryOutOperationEnhanced(models.TransientModel):
    _name = 'enhanced.wizard.invoutopr'

    tanggal_awal = fields.Datetime(string='Start date')
    tanggal_ahir = fields.Datetime(string='End date')

    excel_file = fields.Binary(string='Download Report Excel', readonly="1")
    
    @api.multi
    def process_wizard(self):
        time1 = datetime.strptime(self.tanggal_awal,"%Y-%m-%d %H:%M:%S")
        time2 = datetime.strptime(self.tanggal_ahir,"%Y-%m-%d %H:%M:%S")
        selisih = time2 - time1
        if selisih.days < 0:
            raise UserError('Invalid datetime range')
        else:
            workbook = xlwt.Workbook(encoding="UTF-8")
            worksheet = workbook.add_sheet('INVENTORY OUT OPERATION',cell_overwrite_ok=True)
            style1 = xlwt.easyxf('font: bold True, color black; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color red; align: horiz center;')
            style2 = xlwt.easyxf('font: bold off, color black; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color white;')
            namakolom = ['WAKTU','KODE BARANG','NAMA MATERIAL','CATEGORY','PELANGGAN','NO JARINGAN','COST CENTER','ANALYTIC ACCOUNT','QTY','SATUAN','HARGA SATUAN','TOTAL HARGA','REFERENCE']
            lebarkolom = [18,20,60,40,45,15,25,25,12,12,12,12,18]
            ii = 0
            for kolom in namakolom:
                cols = worksheet.col(ii)
                cols.width = 256 * lebarkolom[ii]
                worksheet.write(0,ii,kolom,style1)
                ii = ii + 1            
            baris = 1
            getmove = self.env['stock.move'].search(['&','&','&',('date','>=',self.tanggal_awal),('date','<=',self.tanggal_ahir),('state','=','done'),('picking_id.idmr','!=',False)])
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            for move in getmove:
                d2 = pytz.utc.localize(datetime.strptime(move.date,"%Y-%m-%d %H:%M:%S")).astimezone(local)
                normlisasi = datetime.strftime(d2,"%Y-%m-%d %H:%M:%S")
                worksheet.write(baris,0,normlisasi,style2)
                produkid = move.product_id
                worksheet.write(baris,1,produkid.default_code,style2)
                worksheet.write(baris,2,produkid.display_name,style2)
                worksheet.write(baris,3,move.kategorix.name,style2)
                cc = move.picking_id
                worksheet.write(baris,4,cc.idmr.task_idx.related_cust.display_name,style2)
                worksheet.write(baris,5,cc.idmr.task_idx.related_nojar,style2)
                worksheet.write(baris,6,move.cost_center_id.name,style2)
                worksheet.write(baris,7,move.analytic_account_id.name,style2)
                worksheet.write(baris,8,move.product_uom_qty,style2)
                worksheet.write(baris,9,move.product_uom.name,style2)
                worksheet.write(baris,10,move.price_unit,style2)
                # worksheet.write(baris,11,move.jumlahx,style2)
                worksheet.write(baris,11,move.value,style2)
                worksheet.write(baris,12,move.reference,style2)
                baris = baris + 1
            fp = BytesIO()
            workbook.save(fp)
            self.excel_file = base64.encodestring(fp.getvalue())
            fp.close()
            return {
                'type' : 'ir.actions.act_url',
                'url' : 'web/content/?model=enhanced.wizard.invoutopr&field=excel_file&download=true&id=%s&filename=laporanOutInventoryOperation.xls'%(self.id),
                'target' : 'new'
            }