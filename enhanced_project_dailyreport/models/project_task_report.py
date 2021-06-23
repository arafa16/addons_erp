from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectTaskReportDaily(models.Model):
    _inherit = 'project.task'

    daily_so_spk = fields.Char(string='NO SPK', related="sale_order_id.spk_sementara")
    daily_so_area_new = fields.Many2one(related='sale_order_id.sales_area_kode',string="Operation Area")
    daily_so_alamat = fields.Char(string='ALAMAT', compute="setalamatpanjang")
    daily_so_alamat_street1 = fields.Char(string='alamat1', related="related_cust.street")
    daily_so_alamat_street2 = fields.Char(string='alamat1', related="related_cust.street2")
    daily_so_alamat_city = fields.Char(string='alamat1', related="related_cust.city")
    daily_so_alamat_zip = fields.Char(string='alamat1', related="related_cust.zip")
    daily_speed = fields.Char(string='SPEED')
    daily_media_akses = fields.Selection([("wireline","WIRELINE"),("wireless","WIRELESS")], string='MEDIA AKSES')
    daily_tgl_mulai = fields.Date(string='TANGGAL MULAI',compute='settglnull',)
    daily_tgl_stop_clock = fields.Date(string='TGL STOPCLOCK')
    daily_tgl_open_clock = fields.Date(string='TGL OPENCLOCK')
    daily_tgl_status = fields.Date(string='TGL STATUS')
    daily_tgl_selesai = fields.Date(string='TGL SELESAI')
    daily_durasi = fields.Integer(string='DURASI (HARI)')
    daily_sdt = fields.Char(string='SDT')
    daily_cp_la = fields.Char(string='CP LA')
    daily_cp_lapangan = fields.Char(string='CP LAPANGAN')
    daily_cp_pelanggan = fields.Char(string='CP PELANGGAN')
    daily_mingguan = fields.Selection([("M1","M1"),("M2","M2"),("M3","M3"),("M4","M4"),("M5","M5")], string='MINGUUAN')
    daily_los = fields.Char(string='LOS')
    daily_alokasi_perangkat = fields.Many2one('alokasi.perangkat', string='ALOKASI PERANGKAT')
    daily_npae = fields.Char(string='LOS')
    daily_perizinan = fields.Char(string='PERIZINAN')
    daily_deposit = fields.Char(string='DEPOSIT')
    daily_supervisi = fields.Char(string='SUPERVISI')
    daily_biaya_sewa = fields.Char(string='BIAYA SEWA')
    daily_ikg = fields.Char(string='IKG')
    daily_sewa_space = fields.Char(string='SEWA SPACE')
    daily_tindak_lanjut = fields.Char(string='TINDAK LANJUT')

    daily_teknisi1 = fields.Many2one('daily.teknisi', string='TEKNISI 1')
    daily_teknisi2 = fields.Many2one('daily.teknisi', string='TEKNISI 2')
    daily_keterangan = fields.Char(string='KETERANGAN')
    daily_terpasang = fields.Char(string='PRNGKT TERPASANG')
    ww = 4
    
    @api.depends()
    def settglnull(self):
        for doc in self:
            if doc.daily_tgl_mulai == False:
                pecah = doc.create_date.split(' ')
                doc.daily_tgl_mulai = pecah[0]
    
    @api.depends()
    def setalamatpanjang(self):
        for doc in self:
            doc.daily_so_alamat = ''
            if doc.daily_so_alamat_street1 != False:
                doc.daily_so_alamat = doc.daily_so_alamat + str(doc.daily_so_alamat_street1)
            if doc.daily_so_alamat_street2 != False:
                doc.daily_so_alamat = doc.daily_so_alamat + ' ' + str(doc.daily_so_alamat_street2)
            if doc.daily_so_alamat_city != False:
                doc.daily_so_alamat = doc.daily_so_alamat + ' ' + str(doc.daily_so_alamat_city)
            if doc.daily_so_alamat_zip != False:
                doc.daily_so_alamat = doc.daily_so_alamat + ' ' + str(doc.daily_so_alamat_zip)