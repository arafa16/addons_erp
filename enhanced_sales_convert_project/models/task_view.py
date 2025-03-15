from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TaskView(models.Model):
    _inherit = 'project.task'

    sale_order_id = fields.Many2one('sale.order', "Sale Order")
    related_date_order = fields.Datetime(related='sale_order_id.date_order', readonly=True)
    related_cust = fields.Many2one(related='sale_order_id.partner_shipping_id', readonly=True)
    related_nojar = fields.Char(related='sale_order_id.nojar', readonly=True, string="Nomor Jaringan", store=True)
    related_proj_type = fields.Many2one('enhanced.sales.project.tabel', string="Jenis Project", related='sale_order_id.proj_type', store=True)
    related_ord_type = fields.Many2one('enhanced.sales.jenis.tabel', string="Jenis Order", related='sale_order_id.ord_type', store=True)
    related_pek_type = fields.Many2one('enhanced.sales.pekerjaan.tabel', string="Jenis Pekerjaan", related='sale_order_id.pek_type', store=True)
    related_team_id = fields.Many2one('crm.team', string='Related Team id', related="sale_order_id.team_id", store=True)
    related_department = fields.Many2one('hr.department', string='Related Departement SO', related="sale_order_id.so_bagian", store=True)
    related_partnerid = fields.Many2one(related='sale_order_id.partner_id', readonly=True)
    related_alias = fields.Char(related='related_partnerid.singkatan',string="Related Area Old", readonly=True,store=True,)
    related_area = fields.Many2one('enhanced.sales.area', string="Operation Area", related='sale_order_id.sales_area_kode', store=True,)
    testx = fields.Integer(string='test field',compute='setAssign',)

    @api.model
    def create(self, vals):
        cc = 4
        return super(TaskView, self).create(vals)

    @api.depends()
    def setAssign(self):
        usert = self.env.ref('enhanced_sales_convert_project.group_projectmr_assign_user').id
        self.testx = usert