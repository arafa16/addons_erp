from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SalesOrderEnhancedProject(models.Model):
    _inherit = 'sale.order'
    nojar = fields.Char(string='Nomor Jaringan')
    proj_type = fields.Many2one('enhanced.sales.project.tabel', string='Jenis Project')
    ord_type = fields.Many2one('enhanced.sales.jenis.tabel', string='Jenis Order')
    pek_type = fields.Many2one('enhanced.sales.pekerjaan.tabel', string='Jenis Pekerjaan')
    sales_area_kode = fields.Many2one('enhanced.sales.area', string='Sales Area')
    jenis_so = fields.Selection(selection_add=[("dtc","Datacom"), ("datacom","Trading")])
