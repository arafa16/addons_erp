from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BudgetAdjustment(models.Model):
    _name = "budget.adjustment"
    _description = "Budget Adjustment"
    _order = "name desc"
    _inherit = ['mail.thread']

    name = fields.Char(string='Budget Adjustment Number', required=True, readonly=True, copy=False, default='/', help='The name that will be used on budget adjustment')
    type = fields.Selection([
        ('transfer', 'Transfer'),
        ('add', 'Additional'),
        ('control', 'Control')
    ], required=True, string='Adjustment Type', default='transfer')
    adjustment_amount = fields.Float(digits=0, string="Adjustment Amount")
    adjustment_restrict = fields.Selection([('allow','Allow'),('restrict' , 'Restricted'),('warn','Warning')], string="Adjustment Control")
    creating_user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    date = fields.Datetime('Date', required=True, index=True, copy=False, default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        # ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft')
    company_id = fields.Many2one('res.company', 'Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.budget.post'))
    budget_line_id_adj = fields.Many2one('crossovered.budget.lines', string='Budget To', ondelete="restrict", readonly=True, domain="[('state', '=', 'ready')]", index=True)
    cost_center_id_adj = fields.Many2one("cost.center", string='Cost Center', compute='get_budget_info')
    analytic_account_id_adj = fields.Many2one('account.analytic.account', string='Analytic Account', compute='get_budget_info')
    date_from_adj = fields.Date('Start Date', compute='get_budget_info')
    date_to_adj = fields.Date('End Date', compute='get_budget_info')
    restrict_allow_adj = fields.Selection([('allow','Allow'),('restrict' , 'Restricted'),('warn','Warning')], string="Budget Control", readonly=True, default="restrict")
    avail_req_amount_adj = fields.Float(digits=0, string="Available Amount", related='budget_line_id_adj.avail_req_amount')

    budget_line_id_src = fields.Many2one('crossovered.budget.lines', string='Budget From', ondelete="restrict", readonly=True, domain="[('state', '=', 'ready')]", index=True)
    cost_center_id_src = fields.Many2one("cost.center", string='Cost Center', compute='get_budget_info')
    analytic_account_id_src = fields.Many2one('account.analytic.account', string='Analytic Account', compute='get_budget_info')
    date_from_src = fields.Date('Start Date', compute='get_budget_info')
    date_to_src = fields.Date('End Date', compute='get_budget_info')
    restrict_allow_src = fields.Selection([('allow','Allow'),('restrict' , 'Restricted'),('warn','Warning')], string="Budget Control", readonly=True, default="restrict")
    avail_req_amount_src = fields.Float(digits=0, string="Available Amount", related='budget_line_id_src.avail_req_amount')
    description = fields.Text(string='Description')

    line_ids = fields.One2many('budget.adjustment.line', 'budget_adjusment_id')

    @api.multi
    def unlink(self):
        for budget in self:
            if budget.state == 'done':
                raise UserError(_("Document is not allowed to be deleted, due to it's status is done."))
        return super(BudgetAdjustment, self).unlink()

    @api.model
    def create(self, vals):
        return super(BudgetAdjustment, self).create(vals)

    @api.multi
    def get_budget_info(self):
        self.cost_center_id_adj = self.budget_line_id_adj.cost_center_id.id
        self.analytic_account_id_adj = self.budget_line_id_adj.analytic_account_id.id
        self.date_from_adj = self.budget_line_id_adj.date_from
        self.date_to_adj = self.budget_line_id_adj.date_to
        self.cost_center_id_src = self.budget_line_id_src.cost_center_id.id
        self.analytic_account_id_src = self.budget_line_id_src.analytic_account_id.id
        self.date_from_src = self.budget_line_id_src.date_from
        self.date_to_src = self.budget_line_id_src.date_to

    @api.multi
    def action_get_budget(self):
        view = self.env.ref('account_budget_kopkarla.view_account_budget_available_tree')
        form = self.env.ref('account_budget_kopkarla.view_account_budget_available_form')
        search_view = self.env.ref('account_budget_kopkarla.view_account_budget_available_search')

        # view = self.env.ref('sh_message.sh_message_wizard')
        # view_id = view and view.id or False
        # action = self.env.context.get('params')['action']
        context = {'budget_adjustment_id': self.id,
                    'budget_position': self.env.context.get('budget_position'),
                }
        domain = [('state', '=', 'ready')]
        if self.env.context.get('budget_position') == 'source':
            if self.cost_center_id_adj:
                domain.append(('cost_center_id', '=', self.cost_center_id_adj.id))
            if self.analytic_account_id_adj:
                domain.append(('analytic_account_id', '=', self.analytic_account_id_adj.id))

            # context.update({'cost_center_adj': self.cost_center_id_adj.id})
            # context.update({'analytic_account_adj': self.analytic_account_id_adj.id})
        return {
            'name': 'Budget Adjustment',
            'type': 'ir.actions.act_window',
            # 'view_type': 'form',
            # 'view_mode': 'tree,form',
            'res_model': 'crossovered.budget.lines',
            'views': [(view.id, 'tree'), (form.id, 'form')],
            # 'view_id': view.id,
            'target': 'current',
            'search_view_id': search_view.id,
            # 'limit': 5,
            'domain': domain,
            'context': context,
        }

    @api.multi
    def _validate(self):
        if not self.budget_line_id_adj:
            raise UserError(_('You have to select a budget to be adjusted.'))
        if self.type == 'control':
            if self.adjustment_restrict == self.restrict_allow_adj:
                raise UserError(_('Adjustment control must be different with budget to adjust.'))
        elif not self.adjustment_amount:
            raise UserError(_('Nilai adjustment tidak boleh 0!!!'))
        # elif self.budget_line_id_src and abs(self.adjustment_amount) > abs(self.avail_req_amount_src):
        #     raise UserError(_('Sisa Budget Source tidak cukup!!!'))
        elif self.adjustment_amount > 0:
            if self.adjustment_amount + self.avail_req_amount_adj > 0:
                raise UserError(_('Sisa Budget to adjust tidak cukup!!!'))
        elif self.adjustment_amount < 0:
            if self.adjustment_amount - self.avail_req_amount_src < 0:
                raise UserError(_('Sisa Budget Source tidak cukup!!!'))

    @api.multi
    def _generate_budget_adjustment_line(self):
        val_adjusted = [{
            'budget_line_id': self.budget_line_id_adj,
            'amount': self.type != 'control' and self.adjustment_amount or False,
            'restrict': self.type == 'control' and self.adjustment_restrict or False,
        }]
        if self.type != 'control':
            val_adjusted.append({
                'budget_line_id': self.budget_line_id_src,
                'amount': self.type != 'control' and -self.adjustment_amount or False,
            })
        else:
            self.budget_line_id_adj.restrict_allow = self.adjustment_restrict

        vals = [[0, 0, line] for line in val_adjusted]
        self.line_ids = vals

    @api.multi
    def action_budget_adjustment_done(self):
        self._validate()
        self._generate_budget_adjustment_line()
        if self.name == '/':
            seq = self.env['ir.sequence'].next_by_code('budget.adjustment') or '/'
            self.name = seq
        self.state = 'done'

    @api.multi
    def action_budget_adjustment_draft(self):
        if self.type == 'control':
            if self.adjustment_restrict != self.budget_line_id_adj.restrict_allow:
                raise UserError(_('Budget can not reset due to it has been adjust after this adjustment.'))
            else:
                self.budget_line_id_adj.restrict_allow = self.restrict_allow_adj
        if abs(self.budget_line_id_adj.avail_req_amount) >= abs(self.adjustment_amount):
            self.line_ids.unlink()
            self.state = 'draft'
        else:
            raise UserError(_("Budget adjustment tidak bisa dibatalkan karena sisa budget kurang dari 0."))


class BudgetAdjustmentLine(models.Model):
    _name = "budget.adjustment.line"
    _description = "Budget Adjustment Lines"
    _rec_name = 'budget_line_id'

    budget_adjusment_id = fields.Many2one('budget.adjustment', string='Budget Adjustment', ondelete="cascade", readonly=True)
    budget_line_id = fields.Many2one('crossovered.budget.lines', string='Budget', ondelete="restrict", readonly=True)
    cost_center_id = fields.Many2one("cost.center", string='Cost Center', compute='get_budget_info')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', compute='get_budget_info')
    date_from = fields.Date('Start Date', compute='get_budget_info')
    date_to = fields.Date('End Date', compute='get_budget_info')
    restrict = fields.Selection([('allow','Allow'),('restrict' , 'Restricted'),('warn','Warning')], string="Adjustment Control")
    amount = fields.Float(digits=0, string="Adjustment Amount")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], string='Status', related='budget_adjusment_id.state')
    budget_line_opponent_id = fields.Many2one('crossovered.budget.lines', string='Budget Opponent', compute='_get_opponent')
    cost_center_opponent_id = fields.Many2one("cost.center", string='Cost Center', compute='_get_opponent')
    analytic_account_opponent_id = fields.Many2one('account.analytic.account', string='Analytic Account', compute='_get_opponent')
    date_from_opponent = fields.Date('Start Date', compute='_get_opponent')
    date_to_opponent = fields.Date('End Date', compute='_get_opponent')
    # restrict = fields.Selection([('allow','Allow'),('restrict' , 'Restricted'),('warn','Warning')], string="Adjustment Control")
    amount_opponent = fields.Float(digits=0, string="Adjustment Amount", compute='_get_opponent')
    posted_date = fields.Datetime('Posted Date', related='budget_adjusment_id.write_date', store=True)

    def _get_opponent(self):
        for line in self:
            line_opponent = line.budget_adjusment_id.line_ids.filtered(lambda l: l.budget_line_id != line.budget_line_id)
            line.budget_line_opponent_id = line_opponent.budget_line_id
            line.cost_center_opponent_id = line_opponent.cost_center_id
            line.analytic_account_opponent_id = line_opponent.analytic_account_id
            line.date_from_opponent = line_opponent.date_from
            line.date_to_opponent = line_opponent.date_to
            line.amount_opponent = line_opponent.amount

    @api.multi
    def get_budget_info(self):
        for line in self:
            line.cost_center_id = line.budget_line_id.cost_center_id.id
            line.analytic_account_id = line.budget_line_id.analytic_account_id.id
            line.date_from = line.budget_line_id.date_from
            line.date_to = line.budget_line_id.date_to
