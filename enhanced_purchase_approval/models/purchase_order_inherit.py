from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import OrderedDict
from datetime import datetime
import pytz  

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    bolehConfirm = fields.Boolean(string='boleh confirm ?')
    setToLoA = fields.Boolean(string='Set To LoA')
    tt = fields.Char(string='temporary dummy')
    apvteks = fields.Char(string='Approval')
    penandatangan = fields.Many2one('hr.employee', string='Approval')
    FakturNomor = fields.Char(string='E-Faktur Number')
    FakturTanggal = fields.Date(string='E-Faktur Date')
    linktracker = fields.Char(string='link tracker')
    langsung = fields.Boolean(string='Direct to Customer')
    langsung_alamat = fields.Char(string='Direct Address')
    isOverdue = fields.Selection([("over","Overdue"),("notover","Not Overdue")], string='Overdue', compute='get_overdue', store=True)
    
    #loa Attribut
    checker1 = fields.Many2one('hr.employee', string='Assman Checker')
    beforecheck = fields.Char(string='State Before Check')
    isassman = fields.Boolean(string='Is Assman ?',compute='getassman',)

    penandatangan1 = fields.Many2one('hr.employee', string='Asisten Manager')
    penandatangan2 = fields.Many2one('hr.employee', string='Manager')
    penandatangan3 = fields.Many2one('hr.employee', string='General Manager')
    penandatangan4 = fields.Many2one('hr.employee', string='Pengurus/Direktur')
    penandatangan5 = fields.Many2one('hr.employee', string='Ketua Pengurus')
    
    required1 = fields.Boolean(string='LoA Level 1', compute="setButtoncheck1")
    required2 = fields.Boolean(string='LoA Level 2', compute="setButtoncheck2")
    required3 = fields.Boolean(string='LoA Level 3', compute="setButtoncheck3")
    required4 = fields.Boolean(string='LoA Level 4', compute="setButtoncheck4")
    required5 = fields.Boolean(string='LoA Level 5', compute="setButtoncheck5")
    loa_request = fields.Selection([(1,"Request LoA to Asisten Manager"),(2,"Request LoA to Manager"),(3,"Request LoA to General manager"),(4,"Request LoA to Pengurus/Direktur"),(5,"Request LoA to Ketua Pengurus"),(10,"Done")], string='Status LoA')
    amount_total_base = fields.Float(string='Total in Company Currency', store=True, compute='_get_amount_total_base')

    def _approval_levels(self):
        """Return active approval levels in sequential order."""
        levels = []
        for level, required, employee in (
                (1, self.required1, self.penandatangan1),
                (2, self.required2, self.penandatangan2),
                (3, self.required3, self.penandatangan3),
                (4, self.required4, self.penandatangan4),
                (5, self.required5, self.penandatangan5)):
            if required and employee.id:
                levels.append((level, employee))
        return levels

    def _approval_start(self):
        """Return the first active approval level."""
        levels = self._approval_levels()
        return levels[0] if levels else False

    @api.multi
    @api.depends('amount_total', 'currency_id')
    def _get_amount_total_base(self):
        for purchase_order in self:
            if purchase_order.currency_id.id != purchase_order.company_id.currency_id.id:
                currency_id = purchase_order.currency_id.with_context(date=purchase_order.date_order)
                purchase_order.amount_total_base = self.compute(currency_id, purchase_order.amount_total,
                                                                                purchase_order.company_id.currency_id)
            else:
                purchase_order.amount_total_base = purchase_order.amount_total

    @api.multi
    def compute(self, currency_id, from_amount, to_currency, round=True):
        """ Convert `from_amount` from currency `self` to `to_currency`. """
        currency_id, to_currency = currency_id or to_currency, to_currency or currency_id
        assert currency_id, "compute from unknown currency"
        assert to_currency, "compute to unknown currency"
        # apply conversion rate
        if currency_id == to_currency:
            to_amount = from_amount
        else:
            to_amount = from_amount * self._get_conversion_rate(currency_id, to_currency)
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency):
        from_currency = from_currency.with_env(self.env)
        to_currency = to_currency.with_env(self.env)
        return to_currency.rate / from_currency.rate

    @api.multi
    def get_overdue(self):
        for doc in self:
            if doc.state == 'purchase':
                doc.isOverdue = 'notover'
                pickingids = doc.picking_ids
                timepicking = ''
                for baris in pickingids:
                    if baris.date_done == False:
                        sekarang = datetime.now(pytz.utc)
                        timepicking = datetime.strftime(sekarang,"%Y-%m-%d %H:%M:%S")
                    else:
                        timepicking = baris.date_done
                if timepicking != '':
                    awal = datetime.strptime(timepicking,"%Y-%m-%d %H:%M:%S")
                    akhir = datetime.strptime(str(doc.date_planned),"%Y-%m-%d %H:%M:%S")
                    selisih = awal - akhir
                    if selisih.days >= 0:
                        doc.isOverdue = 'notover'
                    else:
                        doc.isOverdue = 'over'
                else:
                    doc.isOverdue = 'notover'

    @api.multi
    def getassman(self):
        if self._uid == self.checker1.user_id.id:
            self.isassman = True
        else:
            self.isassman = False
    
    @api.multi
    def _setup_attrs(self, model, name):
        super(fields.Selection, self)._setup_attrs(model, name)
        for field in reversed(fields.resolve_mro(model, name, self._can_setup_from)):
            if 'selection' in field.args:
                self.selection = field.args['selection']
            if 'selection_add' in field.args:
                selection_add = field.args['selection_add']
                self.selection = list(OrderedDict(self.selection + selection_add).items())
            if 'selection_add_after' in field.args:
                selection_add_after = field.args['selection_add_after']
                new_selection = []
                for item in self.selection:
                    new_selection.append(item)
                    items_to_add = selection_add_after.get(item[0],[])
                    for item_to_add in items_to_add:
                        new_selection.append(item_to_add)
                self.selection = list(OrderedDict(new_selection).items())

    fields.Selection._setup_attrs = _setup_attrs

    state = fields.Selection(selection_add_after={'sent': [('assmancheck', 'Assman Check'),('requestloa', 'Request LoA'),('loaconfirmed', 'LoA Confirmed')]})

    @api.depends('order_line')
    def setButtoncheck1(self):
        self.required1 = False
        loa1 = self.env['tabel.ttd.purhchase'].browse(1)
        if loa1.id != False:
            if loa1.batas_atas > 0:
                amount_x = self.amount_total_base
                if loa1.batas_atas <= amount_x:
                    self.required1 = True
                else:
                    if loa1.batas_bawah <= amount_x:
                        self.required1 = True
    
    @api.depends('order_line')
    def setButtoncheck2(self):
        self.required2 = False
        loa2 = self.env['tabel.ttd.purhchase'].browse(2)
        if loa2.id != False:
            if loa2.batas_atas > 0:
                amount_x = self.amount_total_base
                if loa2.batas_atas <= amount_x:
                    self.required2 = True
                else:
                    if loa2.batas_bawah <= amount_x:
                        self.required2 = True
    
    @api.depends('order_line')
    def setButtoncheck3(self):
        self.required3 = False
        loa3 = self.env['tabel.ttd.purhchase'].browse(3)
        if loa3.id != False:
            if loa3.batas_atas > 0:
                amount_x = self.amount_total_base
                if loa3.batas_atas <= amount_x:
                    self.required3 = True
                else:
                    if loa3.batas_bawah <= amount_x:
                        self.required3 = True
    
    @api.depends('order_line')
    def setButtoncheck4(self):
        self.required4 = False
        loa4 = self.env['tabel.ttd.purhchase'].browse(4)
        if loa4.id != False:
            if loa4.batas_atas > 0:
                amount_x = self.amount_total_base
                if loa4.batas_atas <= amount_x:
                    self.required4 = True
                else:
                    if loa4.batas_bawah <= amount_x:
                        self.required4 = True

    @api.depends('order_line')
    def setButtoncheck5(self):
        self.required5 = False
        loa5 = self.env['tabel.ttd.purhchase'].browse(5)
        if loa5.id != False:
            if loa5.batas_atas > 0:
                amount_x = self.amount_total_base
                if loa5.batas_atas <= amount_x:
                    self.required5 = True
                else:
                    if loa5.batas_bawah <= amount_x:
                        self.required5 = True
    
    @api.multi
    def button_action_request_loa_confirm(self):
        if self._uid == self.checker1.user_id.id:
            start = self._approval_start()
            if not start:
                raise UserError('Tidak ada level approval yang aktif')

            start_level, start_employee = start
            tail = {
                1: 'Asisten Manager',
                2: 'Manager',
                3: 'General Manager',
                4: 'Pengurus/Direktur',
                5: 'Ketua Pengurus',
            }.get(start_level, '')
            tujuan = [start_employee.user_id.email]

            self.loa_request = start_level
            self.setToLoA = True
            self.apvteks = tail
            self.state = 'requestloa'
            self._sent_mail(tujuan, 'purchase_order_loa', tail)
        else:
            raise UserError('Access Denied, Only User Checker can Request LoA Action')

    @api.multi
    def _sent_mail(self, mailto = [], template = '', tail=''):
        if len(mailto) > 0:
            penerima = ''
            ii = 0
            for terima in mailto:
                if ii == 0:
                    penerima = terima
                if ii > 0:
                    penerima = penerima + ';' + terima
                ii = ii + 1
            getmail = self.sudo().env['ir.mail_server'].search([('sequence','<=',10)])
            if len(getmail) > 0 and len(mailto) > 0:
                sendermail = getmail[0].smtp_user
                template_browse = self.sudo().env['mail.template'].search([('name','=',template)])
                if template_browse.id != False:
                    base_url = self.sudo().env['ir.config_parameter'].get_param('web.base.url')
                    base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
                    self.linktracker = base_url
                    kk = template_browse.generate_email(self.id,fields=None)
                    kk['email_to'] = penerima
                    kk['email_from'] = sendermail
                    kk['res_id'] = False
                    mail_obj = self.sudo().env['mail.mail']
                    msg_id = mail_obj.create(kk)
                    if tail != '':
                        msg_id.subject = msg_id.subject +' '+ str(tail)
                    msg_id.send()
        return True
    
    @api.multi
    def button_set_to_loa(self):
        if len(self.penandatangan) > 0:
            getmail = self.sudo().env['ir.mail_server'].search([('sequence','<=',10)])
            sendermail = ''
            if len(getmail) > 0:
                sendermail = getmail[0].smtp_user
            mailto = self.penandatangan.user_id.email
            template_browse = self.sudo().env['mail.template'].search([('name','=','purchase_order_loa')])
            if template_browse.id != False:
                base_url = self.sudo().env['ir.config_parameter'].get_param('web.base.url')
                base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
                self.linktracker = base_url
                kk = template_browse.generate_email(self.id,fields=None)
                kk['email_to'] = mailto
                kk['email_from'] = sendermail
                kk['res_id'] = False
                mail_obj = self.sudo().env['mail.mail']
                msg_id = mail_obj.create(kk)  
                msg_id.send()
            self.setToLoA = True
            ww = 4
        else:
            raise UserError('Otoritas Tanda tangan belum diset')
    
    @api.multi
    def button_cancel(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state == 'done':
                    raise UserError(_('Unable to cancel purchase order %s as some receptions have already been done.') % (order.name))
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(_("Unable to cancel this purchase order. You must first cancel related vendor bills."))

            # If the product is MTO, change the procure_method of the the closest move to purchase to MTS.
            # The purpose is to link the po that the user will manually generate to the existing moves's chain.
            if order.state in ('draft', 'sent', 'to approve','assmancheck','requestloa','loaconfirmed'):
                for order_line in order.order_line:
                    if order_line.move_dest_ids:
                        move_dest_ids = order_line.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
                        siblings_states = (move_dest_ids.mapped('move_orig_ids')).mapped('state')
                        if all(state in ('done', 'cancel') for state in siblings_states):
                            move_dest_ids.write({'procure_method': 'make_to_stock'})
                            move_dest_ids._recompute_state()

            for pick in order.picking_ids.filtered(lambda r: r.state != 'cancel'):
                pick.action_cancel()

            order.order_line.write({'move_dest_ids':[(5,0,0)]})

            order.setToLoA = False
            order.bolehConfirm = False
            order.loa_request = False
            order.write({'state': 'cancel'})
    
    @api.multi
    def button_action_assman_check(self):
        if self.checker1.id != False:
            tujuan  = []
            teksmail = self.checker1.user_id.email
            tujuan.append(teksmail)
            template = 'purchase_order_assman'
            self.beforecheck = self.state
            self.state = 'assmancheck'
            self._sent_mail(tujuan, template,'')
        else:
            raise UserError('Checker Assaman Belum diset')
    
    @api.multi
    def button_action_assman_set_draft(self):
        if self._uid == self.checker1.user_id.id:
            if self.beforecheck == False or self.beforecheck == '':
                self.state = 'draft'
            else:
                self.state = self.beforecheck
        else:
            raise UserError('Access Denied, Only User Checker can Set to Draft Action')

    @api.multi
    def press_approval(self):
        levels = self._approval_levels()
        if not levels:
            raise UserError('Tidak ada level approval yang aktif')

        current_index = next(
            (index for index, item in enumerate(levels)
             if item[0] == self.loa_request),
            None)
        if current_index is None:
            raise UserError('LoA Confirm, Access Denied')

        current_employee = levels[current_index][1]
        next_level = False
        next_employee = False
        tail = ''
        tujuan = []
        tailoroginal = self.apvteks

        if current_employee.user_id.id == self._uid:
            if current_index + 1 < len(levels):
                next_level, next_employee = levels[current_index + 1]
                tail = {
                    2: 'Manager',
                    3: 'General Manager',
                    4: 'Pengurus/Direktur',
                    5: 'Ketua Pengurus',
                }.get(next_level, '')
                tujuan.append(next_employee.user_id.email)

            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.message_post(body="Document LoA Level " + str(tailoroginal) + " Approved By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")

            if next_level:
                self.apvteks = tail
                self.loa_request = next_level
                template = 'purchase_order_loa'
                self._sent_mail(tujuan, template,tail)
            else:
                tujuan.append(self.create_uid.email)
                self.apvteks = 'done'
                self.loa_request = 10
                self.bolehConfirm = True
                self.state = 'loaconfirmed'
                template = 'purchase_order_ready_to_tonfirm'
                self._sent_mail(tujuan, template,'')
        else:
            raise UserError('LoA Confirm, Access Denied')
    
    @api.multi
    def button_confirm(self):
        ww = self.name.replace('RFQ','PO')
        self.name = ww
        vv = self.env['sprogroup.purchase.request'].search([('nomor_bidding','=',self.requisition_id.id)])
        isidata = []
        isipom2o = []
        isinya = []
        sudahada = False
        for pox in vv.nomor_po_m2o:
            isinya.append(pox.id)
            if pox.id == self.id:
                sudahada = True
        if sudahada == False:
            isinya.append(self.id)
        isipom2o.append(6)
        isipom2o.append(False)
        isipom2o.append(isinya)
        isidata.append(isipom2o)
        invokepr = {}
        invokepr['nomor_po_m2o'] = isidata
        # vv.idpo = self.id
        vv.write(invokepr)
        
        for order in self:
            if order.state not in ['loaconfirmed']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    @api.multi
    def button_draft(self):
        ww = self.name.replace('PO','RFQ')
        self.name = ww
        return super(PurchaseOrderInherit, self).button_draft()