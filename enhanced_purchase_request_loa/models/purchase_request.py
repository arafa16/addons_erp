from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseReqeustLOAInherit(models.Model):
    _inherit = 'sprogroup.purchase.request'

    bolehConfirm = fields.Boolean(string='LOA Confirm')
    isDispatch = fields.Boolean(string='Sudah di dispatch?')
    temp_dummy = fields.Char(string='temporary dummy')
    apvteks = fields.Char(string='LoA Confirm')
    penandatangan = fields.Many2one('hr.employee', string='Approval')
    eksekutor = fields.Many2one('res.users', string='Penanggung Jawab')
    testx = fields.Integer(string='test field',compute='setdomain',)
    budget_ref = fields.Integer(string='field ref budget',compute='setdomain')
    setConfirmLoA = fields.Boolean(string='LOA Button COnfirm')
    coannya = fields.Many2one('account.account', string='Chart of Account')
    # new loa
    tanggal_procure = fields.Date(string='Tanggal Procure')
    issasman = fields.Boolean(string='is assman?', compute='cekassman',)
    assman = fields.Many2one('hr.employee', string='Assman Checker')
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

    def test_function(self):
        vv = self.env['mail.tracking.value'].search([('new_value_char','=','Procure Received')])
        for getpr in vv:
            nomorPr = getpr.mail_message_id.record_name
            if nomorPr != False:
                waktu = getpr.create_date
                pecah = waktu.split(' ')
                tanggal = pecah[0]
                getPrOri = self.env['sprogroup.purchase.request'].search([('name','=',nomorPr)])
                if len(getPrOri) > 0:
                    if getPrOri.tanggal_procure == False:
                        getPrOri.tanggal_procure = tanggal
    

    @api.depends('line_ids')
    def setButtoncheck1(self):
        nn = 1
        for doc in self:
            if nn == 1:
                doc.required1 = False
                loa1 = doc.env['tabel.ttd.purhchase'].browse(1)
                if loa1.id != False:
                    if loa1.batas_atas > 0:
                        amount_x = 0
                        for baris in doc.line_ids:
                            amount_temp = baris.product_qty *  baris.cost_product
                            amount_x = amount_x +  amount_temp
                        if loa1.batas_atas <= amount_x:
                            doc.required1 = True
                        else:
                            if loa1.batas_bawah <= amount_x:
                                doc.required1 = True
            nn = nn + 1
    
    @api.depends('line_ids')
    def setButtoncheck2(self):
        nn = 1
        for doc in self:
            if nn == 1:
                doc.required2 = False
                loa2 = doc.env['tabel.ttd.purhchase'].browse(2)
                if loa2.id != False:
                    if loa2.batas_atas > 0:
                        amount_x = 0
                        for baris in doc.line_ids:
                            amount_temp = baris.product_qty *  baris.cost_product
                            amount_x = amount_x +  amount_temp
                        if loa2.batas_atas <= amount_x:
                            doc.required2 = True
                        else:
                            if loa2.batas_bawah <= amount_x:
                                doc.required2 = True
            nn = nn + 1
    
    @api.depends('line_ids')
    def setButtoncheck3(self):
        nn = 1
        for doc in self:
            if nn == 1:
                doc.required3 = False
                loa3 = doc.env['tabel.ttd.purhchase'].browse(3)
                if loa3.id != False:
                    if loa3.batas_atas > 0:
                        amount_x = 0
                        for baris in doc.line_ids:
                            amount_temp = baris.product_qty *  baris.cost_product
                            amount_x = amount_x +  amount_temp
                        if loa3.batas_atas <= amount_x:
                            doc.required3 = True
                        else:
                            if loa3.batas_bawah <= amount_x:
                                doc.required3 = True
            nn = nn + 1
    
    @api.depends('line_ids')
    def setButtoncheck4(self):
        nn = 1
        for doc in self:
            if nn == 1:
                doc.required4 = False
                loa4 = doc.env['tabel.ttd.purhchase'].browse(4)
                if loa4.id != False:
                    if loa4.batas_atas > 0:
                        amount_x = 0
                        for baris in doc.line_ids:
                            amount_temp = baris.product_qty *  baris.cost_product
                            amount_x = amount_x +  amount_temp
                        if loa4.batas_atas <= amount_x:
                            doc.required4 = True
                        else:
                            if loa4.batas_bawah <= amount_x:
                                doc.required4 = True
            nn = nn + 1
    
    @api.depends('line_ids')
    def setButtoncheck5(self):
        nn = 1
        for doc in self:
            if nn == 1:
                doc.required5 = False
                loa5 = doc.env['tabel.ttd.purhchase'].browse(5)
                if loa5.id != False:
                    if loa5.batas_atas > 0:
                        amount_x = 0
                        for baris in doc.line_ids:
                            amount_temp = baris.product_qty *  baris.cost_product
                            amount_x = amount_x +  amount_temp
                        if loa5.batas_atas <= amount_x:
                            doc.required5 = True
                        else:
                            if loa5.batas_bawah <= amount_x:
                                doc.required5 = True
            nn = nn + 1

        # if loaTabel.id != False:
        #     getTabelToa = self.env['tabel.ttd.purhchase'].search(['&',('id','<=',loaTabel.id),('batas_atas','>',0)])
        #     self.required1 = False
        #     self.required2 = False
        #     self.required3 = False
        #     self.required4 = False
        #     self.required5 = False
        #     updatedata = {}
        #     for loa in getTabelToa:
        #         if loa.urutan == 1:
        #             updatedata['required1'] = True
        #         if loa.urutan == 2:
        #             updatedata['required2'] = True
        #         if loa.urutan == 3:
        #             updatedata['required3'] = True
        #         if loa.urutan == 4:
        #             updatedata['required4'] = True
        #         if loa.urutan == 5:
        #             updatedata['required5'] = True
        # return super(PurchaseReqeustLOAInherit, self).compute_total()
        # self.write(updatedata)

    @api.multi
    def cekassman(self):
        if self.assman.user_id.id == self._uid:
            self.issasman = True
        else:
            self.issasman = False

    @api.multi
    def button_action_assman_check(self):
        tujuan = []
        tujuan.append(self.assman.user_id.email)
        template = 'purchase_request_assman'
        tail = ''
        self._sent_mail(tujuan, template,tail)
        self.state = 'assman_check'

    @api.multi
    def button_action_assman_rejected(self):
        if self.assman.user_id.id == self._uid:
            self.state = 'draft'
        else:
            raise UserError('Access Denied')

    @api.multi
    def button_action_request_budget_check(self):
        if self.assman.user_id.id == self._uid:
            tujuan = []
            tujuan.append(self.assigned_to.email)
            template = 'purchase_request_budget'
            tail = ''
            self._sent_mail(tujuan, template,tail)
            self.state = 'to_approve'
        else:
            raise UserError('Access Denied')
            
    @api.multi
    def button_action_request_budget_reject(self):
        self.mapped('line_ids').do_cancel()
        return self.write({'state': 'rejected'})

    @api.multi
    def button_action_request_budget_confirm(self):
        if self.coannya.id == False:
            raise UserError('Chart of Account belum diset')
        else:
            if self.assigned_to.id == self._uid:
                start = self._approval_start()
                if not start:
                    raise UserError('Tidak ada level approval yang aktif')

                start_level, start_employee = start
                tujuan = [start_employee.user_id.email]
                tail = {
                    1: 'Asisten Manager',
                    2: 'Manager',
                    3: 'General Manager',
                    4: 'Pengurus/Direktur',
                    5: 'Ketua Pengurus',
                }.get(start_level, '')

                self.loa_request = start_level
                self.setConfirmLoA = True
                self.apvteks = tail
                self.state = 'leader_request'
                self._sent_mail(tujuan, 'purchase_request_loa', tail)
            else:
                raise UserError('Access Denied')
    
    @api.multi
    def button_action_request_loa_reject(self):
        if self.loa_request == 1:
            curent = self.penandatangan1
        if self.loa_request == 2:
            curent = self.penandatangan2
        if self.loa_request == 3:
            curent = self.penandatangan3
        if self.loa_request == 4:
            curent = self.penandatangan4
        if self.loa_request == 5:
            curent = self.penandatangan5
        if curent.user_id.id == self._uid:
            self.mapped('line_ids').do_cancel()
            self.state = 'rejected'
            self.loa_request = False
            self.setConfirmLoA = False
            self.apvteks = ''
            self.penandatangan = False
        else:
            raise UserError('LoA Reject, Access Denied')

    @api.multi
    def press_approval_bertingkat(self):
        levels = self._approval_levels()
        if not levels:
            raise UserError('Tidak ada level approval yang aktif')

        current_index = next(
            (index for index, item in enumerate(levels)
             if item[0] == self.loa_request),
            None)
        if current_index is None:
            raise UserError('LoA Confirm, Access Denied')

        current_level, current_employee = levels[current_index]
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
                self.penandatangan = next_employee.id

            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.message_post(body="Document LoA Level " + str(tailoroginal) + " Approved By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")

            if next_level:
                self.apvteks = tail
                self.loa_request = next_level
                template = 'purchase_request_loa'
                self._sent_mail(tujuan, template,tail)
            else:
                idprocure = self.sudo().env.ref('sprogroup_purchase_request.group_purchase_request_buyer').id
                listprocure = self.env['res.users'].search([('groups_id','in',[idprocure])])
                for usernya in listprocure:
                    tujuan.append(usernya.email)
                self.apvteks = 'done'
                self.loa_request = 10
                self.bolehConfirm = True
                self.state = 'leader_approved'
                template = 'purchase_request_procure'
                self._sent_mail(tujuan, template,'')
        else:
            raise UserError('LoA Confirm, Access Denied')
    
    @api.multi
    def button_action_request_procure_reject(self):
        self.mapped('line_ids').do_cancel()
        self.state = 'rejected'
        self.loa_request = False
        self.setConfirmLoA = False
        self.bolehConfirm = False
        self.apvteks = ''
    
    @api.multi
    def button_action_request_procure_receive(self):
        if self.eksekutor.id == False:
            raise UserError('Set Eksekutor RFQ (filed assign to belum diisi)')
        else:
            tujuan = []
            tujuan.append(self.eksekutor.email)
            self.state = 'done'
            self.isDispatch = True
            self.tanggal_procure = fields.Date.today()
            template = 'purchase_request_to_rfq'
            self._sent_mail(tujuan, template,'')
  
    @api.multi
    def button_action_set_to_draft(self):
        self.mapped('line_ids').do_uncancel()
        return self.write({'state': 'draft'})

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
                template_browse = self.sudo().env['mail.template'].search([('name','=',template)], limit=1)
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
    
    @api.depends('date_start')
    def setdomain(self):
        usert = self.env.ref('sprogroup_purchase_request.group_purchase_request_eksekutor').id
        userb = self.env.ref('sprogroup_purchase_request.group_purchase_request_budget').id
        self.testx = usert
        self.budget_ref = userb

    # new loa
    #end of LoA 

    
    # @api.onchange('eksekutor')
    # def set_filtergrup(self):
    #     ww = 4
    #     # users = self.env.ref('group_name').users.ids
    #     # return {'domain': {'field_name': [('id', 'in', users)]}}
    
    @api.multi
    def set_to_loa(self):
        if len(self.penandatangan) > 0:
            getmail = self.sudo().env['ir.mail_server'].search([('sequence','<=',10)])
            sendermail = ''
            if len(getmail) > 0:
                sendermail = getmail[0].smtp_user
            mailto =self.penandatangan.user_id.email
            ww = 4
            template_browse = self.sudo().env['mail.template'].search([('name','=','purchase_request_loa')])
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
            ww = 4
            self.setConfirmLoA = True
        else:
            raise UserError('Approval LOA belum diset')
    
    def set_to_loa_bertingkat(self):
        # set loa to level 1
        if self.penandatangan1.id != False:
            getmail = self.sudo().env['ir.mail_server'].search([('sequence','<=',10)])
            sendermail = ''
            if len(getmail) > 0:
                sendermail = getmail[0].smtp_user
            mailto =self.penandatangan1.user_id.email
            template_browse = self.sudo().env['mail.template'].search([('name','=','purchase_request_loa')])
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
                msg_id.subject = msg_id.subject + str(' Asisten Manager')
                msg_id.send()
            self.write({'loa_request':1,'setConfirmLoA':True})
            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.message_post(body="Document LoA Requested  By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")
        else:
            raise UserError('Approval LoA Level Assisten Manager belum di set.')
    
    @api.multi
    def set_to_loa_bertingkat_reject(self):
        proses = False
        if self.loa_request == 1:
            if self.penandatangan1.user_id.id == self._uid:
                proses = True
        if self.loa_request == 2:
            if self.penandatangan2.user_id.id == self._uid:
                proses = True
        if self.loa_request == 3:
            if self.penandatangan3.user_id.id == self._uid:
                proses = True
        if self.loa_request == 4:
            if self.penandatangan4.user_id.id == self._uid:
                proses = True
        if self.loa_request == 5:
            if self.penandatangan5.user_id.id == self._uid:
                proses = True

        if proses == True:
            self.write({'loa_request':False,'setConfirmLoA':False,'state':'draft'})
            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.message_post(body="Document LoA Rejected  By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")
        else:
            raise UserError("You don't have access to Reject this Document")


    def button_draft(self):
        self.mapped('line_ids').do_uncancel()
        return self.write({'state': 'draft','bolehConfirm': False, 'setConfirmLoA': False, 'isDispatch':False})

    def button_receivebuyer(self):
        self.isDispatch = True
        return super(PurchaseReqeustLOAInherit,self).button_receivebuyer()
    
    
        # cc = self.env['tabel.ttd.purhchase'].search([('batas_atas','>=',self.amount_total)])
        # if len(cc) > 0:
        #     self.apvteks = cc[0].name
    
    @api.multi
    def press_approval(self):
        if len(self.penandatangan) > 0:
            if self.penandatangan.user_id.id == self._uid:
                getmail = self.sudo().env['ir.mail_server'].search([('sequence','<=',10)])
                sendermail = ''
                if len(getmail) > 0:
                    sendermail = getmail[0].smtp_user
                mailto = self.assigned_to.email
                mailto = mailto +';'+ self.requested_by.email
                template_browse = self.sudo().env['mail.template'].search([('name','=','purchase_request_budget')])
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
                self.bolehConfirm = True
                self.write({'state': 'to_approve'})
                idusr = self._uid
                getusrs = self.env['res.users'].browse(idusr)
                self.message_post(body="Document Approved  By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>, Document Ready to Confirm")
            else:
                raise UserError("You don't have access to Approve this document")
        else:
            raise UserError('Approval LOA belum diset')