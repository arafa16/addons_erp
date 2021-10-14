from odoo import fields, models, api, _
from odoo.exceptions import UserError
import base64
import xlwt
import pytz
from io import BytesIO
from pprint import pprint
from datetime import datetime

class InventoryValueationEnhanced(models.TransientModel):
    _name = 'enhanced.wizard.invalin'

    tanggal = fields.Date(string='Tanggal')

    excel_file = fields.Binary(string='Download Report Excel', readonly="1")
    
    @api.multi
    def process_wizard(self):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        awal = datetime.strptime(str(self.tanggal)+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        awal_local = local.normalize(local.localize(awal)).astimezone(pytz.utc)
        awal_time = datetime.strftime(awal_local,"%Y-%m-%d %H:%M:%S")
        akhir = datetime.strptime(str(self.tanggal)+' 23:59:59',"%Y-%m-%d %H:%M:%S")
        akhir_local = local.normalize(local.localize(akhir)).astimezone(pytz.utc)
        akhir_time = datetime.strftime(akhir_local,"%Y-%m-%d %H:%M:%S")
        # set to execel
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet('INVENTORY IN',cell_overwrite_ok=True)
        style0 = xlwt.easyxf('font: bold True, color black; align: horiz center;')
        style1 = xlwt.easyxf('font: bold True, color black; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color green; align: horiz center;')
        style2 = xlwt.easyxf('font: bold off, color black; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color white;')
        namakolom = ['No','WAKTU','NOMOR PR','PEMBUAT PR','DIVISI','COST CENTER','ANALYTIC ACCOUNT','NO PO','NAMA BARANG','JUMLAH','SATUAN','HARGA SATUAN','TOTAL HARGA BELI','STATUS','REFERENCE']
        lebarkolom = [10,15,12,15,20,25,25,12,60,12,20,25,25,20,20]
        ii = 0
        worksheet.write_merge(0,0,0,10,('Tanggal '+str(self.tanggal)),style0)
        for kolom in namakolom:
            cols = worksheet.col(ii)
            cols.width = 256 * lebarkolom[ii]
            worksheet.write(1,ii,kolom,style1)
            ii = ii + 1
        
        getmove = self.env['stock.move'].search(['&','&','&','&',('date','>=',awal_time),('date','<=',akhir_time),('state','=','done'),('location_id.usage','!=','internal'),('location_dest_id.usage','=','internal')])
        jj = 2
        for move in getmove:
            worksheet.write(jj,0,str(jj-1),style2)
            d2 = pytz.utc.localize(datetime.strptime(move.date,"%Y-%m-%d %H:%M:%S")).astimezone(local)
            normlisasi = datetime.strftime(d2,"%Y-%m-%d %H:%M:%S")
            worksheet.write(jj,1,normlisasi,style2)
            pr = move.picking_id.purchase_id.requisition_id.nomor_pr
            worksheet.write(jj,2,pr.name,style2)
            worksheet.write(jj,3,pr.requested_by.display_name,style2)
            divisi = ''
            get_employee = pr.requested_by.employee_ids
            if len(get_employee) > 0:
                namadivisi = get_employee[0].department_id.display_name
                if namadivisi != False:
                    divisi = namadivisi
            worksheet.write(jj,4,divisi,style2)
            worksheet.write(jj,5,move.cost_center_id.name,style2)
            worksheet.write(jj,6,move.analytic_account_id.name,style2)
            worksheet.write(jj,7,move.picking_id.purchase_id.display_name,style2)
            worksheet.write(jj,8,move.product_id.display_name,style2)
            worksheet.write(jj,9,move.product_qty,style2)
            worksheet.write(jj,10,move.product_uom.name,style2)
            datapo_line = move.picking_id.purchase_id.order_line
            harga = 0
            for barispo in datapo_line:
                if barispo.product_id.id == move.product_id.id:
                    harga = barispo.price_unit
            worksheet.write(jj,11,harga,style2)
            rumus = harga * move.product_qty
            worksheet.write(jj,12,rumus,style2)
            if move.picking_id.purchase_id.langsung == True:
                worksheet.write(jj,13,'Direct to Customer',style2)
            else:
                worksheet.write(jj,13,'Internal Location',style2)
            worksheet.write(jj,14,move.reference,style2)
            jj = jj + 1

        fp = BytesIO()
        workbook.save(fp)
        self.excel_file = base64.encodestring(fp.getvalue())
        fp.close()
        return {
            'type' : 'ir.actions.act_url',
            'url' : 'web/content/?model=enhanced.wizard.invalin&field=excel_file&download=true&id=%s&filename=laporanIn.xls'%(self.id),
            'target' : 'new'
        }
        # else:
        #     
        #     
        #     
        #     
        #     
        #     ii = 0
        #     for kolom in namakolom:
        #         cols = worksheet.col(ii)
        #         cols.width = 256 * lebarkolom[ii]
        #         if ii < 5 or ii > 13:
        #             worksheet.write_merge(0,1,ii,ii,kolom,style1)
        #         else:
        #             if ii == 5 or ii == 8 or ii == 11:
        #                 worksheet.write_merge(0,0,ii,(ii+2),kolom,style1)
        #                 worksheet.write(1,ii,'QTY',style1)
        #                 worksheet.write(1,(ii+1),'FROM',style1)
        #                 worksheet.write(1,(ii+2),'TO',style1)
        #         ii = ii + 1
        #     ii = 2
        #     getmove = self.env['stock.move'].search(['&','&',('date','>=',self.tanggal_awal),('date','<=',self.tanggal_ahir),('state','=','done')])
        #     user_tz = self.env.user.tz or pytz.utc
        #     local = pytz.timezone(user_tz)
        #     for move in getmove:
        #         d2 = pytz.utc.localize(datetime.strptime(move.date,"%Y-%m-%d %H:%M:%S")).astimezone(local)
        #         normlisasi = datetime.strftime(d2,"%Y-%m-%d %H:%M:%S")
        #         nama = ''
        #         if len(move.product_id.attribute_value_ids) == 0:
        #             nama = move.product_id.name
        #         else:
        #             nama = move.product_id.name + '['+move.product_id.attribute_value_ids[0].name+']'
        #         worksheet.write(ii,0,normlisasi,style2)
        #         worksheet.write(ii,1,nama,style2)
        #         worksheet.write(ii,2,move.product_uom.name,style2)
        #         worksheet.write(ii,3,move.kategorix.name,style2)
        #         kueriplus = "SELECT coalesce(SUM(stock_move.product_uom_qty),0) AS jumlah FROM stock_move LEFT JOIN stock_location dari ON dari.id = stock_move.location_id LEFT JOIN stock_location menuju ON menuju.id = stock_move.location_dest_id WHERE stock_move.product_id = '" + str(move.product_id.id) + "' AND stock_move.date < '" + str(move.date) + "' AND stock_move.state = 'done' AND dari.usage != 'internal' AND menuju.usage = 'internal'"
        #         kueriminus = "SELECT coalesce(SUM(stock_move.product_uom_qty),0) AS jumlah FROM stock_move LEFT JOIN stock_location dari ON dari.id = stock_move.location_id LEFT JOIN stock_location menuju ON menuju.id = stock_move.location_dest_id WHERE stock_move.product_id = '" + str(move.product_id.id) + "' AND stock_move.date < '" + str(move.date) + "' AND stock_move.state = 'done' AND dari.usage = 'internal' AND menuju.usage != 'internal'"
        #         awalplus = 0
        #         awalminus = 0
        #         awalx = 0
        #         self._cr.execute(kueriplus)
        #         query_plus = self._cr.dictfetchall()
        #         if len(query_plus) > 0:
        #             awalplus = query_plus[0].get('jumlah',0)
        #         self._cr.execute(kueriminus)
        #         query_minus = self._cr.dictfetchall()
        #         if len(query_minus) > 0:
        #             awalminus = query_minus[0].get('jumlah',0)
        #         awalx = awalplus - awalminus
        #         akhirx = awalx
        #         worksheet.write(ii,4,awalx,style2)
        #         if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'internal':
        #             worksheet.write(ii,5,'',style2)
        #             worksheet.write(ii,6,'',style2)
        #             worksheet.write(ii,7,'',style2)
        #             worksheet.write(ii,8,move.product_uom_qty,style2)
        #             worksheet.write(ii,9,move.location_id.display_name,style2)
        #             worksheet.write(ii,10,move.location_dest_id.display_name,style2)
        #             worksheet.write(ii,11,'',style2)
        #             worksheet.write(ii,12,'',style2)
        #             worksheet.write(ii,13,'',style2)
        #         if move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal':
        #             worksheet.write(ii,5,move.product_uom_qty,style2)
        #             worksheet.write(ii,6,move.location_id.display_name,style2)
        #             worksheet.write(ii,7,move.location_dest_id.display_name,style2)
        #             akhirx = awalx + move.product_uom_qty
        #             worksheet.write(ii,8,'',style2)
        #             worksheet.write(ii,9,'',style2)
        #             worksheet.write(ii,10,'',style2)
        #             worksheet.write(ii,11,'',style2)
        #             worksheet.write(ii,12,'',style2)
        #             worksheet.write(ii,13,'',style2)
        #         if move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal':
        #             worksheet.write(ii,5,'',style2)
        #             worksheet.write(ii,6,'',style2)
        #             worksheet.write(ii,7,'',style2)
        #             worksheet.write(ii,8,'',style2)
        #             worksheet.write(ii,9,'',style2)
        #             worksheet.write(ii,10,'',style2)
        #             worksheet.write(ii,11,move.product_uom_qty,style2)
        #             worksheet.write(ii,12,move.location_id.display_name,style2)
        #             worksheet.write(ii,13,move.location_dest_id.display_name,style2)
        #             akhirx = awalx - move.product_uom_qty
        #         worksheet.write(ii,14,akhirx,style2)
        #         worksheet.write(ii,15,move.price_unit,style2)
        #         worksheet.write(ii,16,move.jumlahx,style2)
        #         worksheet.write(ii,17,move.reference,style2)
        #         ii = ii + 1
        #     fp = BytesIO()
        #     workbook.save(fp)
        #     self.excel_file = base64.encodestring(fp.getvalue())
        #     fp.close()

        #     return {
        #         'type' : 'ir.actions.act_url',
        #         'url' : 'web/content/?model=enhanced.wizard.inval&field=excel_file&download=true&id=%s&filename=laporanStockableInOutInventory.xls'%(self.id),
        #         'target' : 'new'
        #     }