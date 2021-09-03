from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
# from lxml import etree
# from odoo.osv.orm import setup_modifiers
# from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
# from odoo.http import request


class AssetBalanceReport(models.Model):
    _name = "asset.balance.report"
    _description = "Asset Balance Report"
    # _order = "date desc, id desc"

    asset_id = fields.Many2one('account.asset.asset', 'Asset')
    code = fields.Char(string='Reference', size=32)
    category_id = fields.Many2one('account.asset.category', string='Category')
    cost_center_id = fields.Many2one("cost.center", string='Cost Center')
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account')
    account_id = fields.Many2one('account.account', 'Account')
    acquisition_date = fields.Date(string='Acquisition Date')
    acquisition_amount = fields.Float(string='Acquisition Amount', digits=0)
    state = fields.Selection([('draft', 'Draft'), ('open', 'Running'), ('close', 'Close'), ('disposed', 'Disposed'),
                              ('sale', 'Sale'), ('reclass', 'Reclass')], 'Status')
    total_last_depre = fields.Float(string='Total Last Depreciation', digits=0)
    jan = fields.Float(string='Jan', digits=0)
    feb = fields.Float(string='Feb', digits=0)
    mar = fields.Float(string='Mar', digits=0)
    apr = fields.Float(string='Apr', digits=0)
    may = fields.Float(string='May', digits=0)
    jun = fields.Float(string='Jun', digits=0)
    jul = fields.Float(string='Jul', digits=0)
    aug = fields.Float(string='Aug', digits=0)
    sep = fields.Float(string='Sep', digits=0)
    oct = fields.Float(string='Oct', digits=0)
    nov = fields.Float(string='Nov', digits=0)
    dec = fields.Float(string='Dec', digits=0)
    this_year_depre = fields.Float(string='Total Year Depreciation', digits=0)
    book_value = fields.Float(string='Book Value', digits=0)
    sale_date = fields.Date(string="Sale date")
    disposal_date = fields.Date(string="Disposal date")

    # @api.multi
    # def budget_request_approve_action(self):
    #     msg = ''
    #     is_approved = True
    #     if self.env.context.get('force') == 0:
    #         for req in self.line_ids:
    #             if req.restrict_allow != 'allow':
    #                 if req.requested_amount > req.available_budget:
    #                     msg = (req.selected_budget_id and '%sRequested amount on %s is larger than available budget.\n' % (msg, req.budget_account_id.name)) or \
    #                           '%sAccount %s has no budget selected.\n' % (msg, req.budget_account_id.name)
    #                     if req.restrict_allow == 'restrict' or not req.selected_budget_id:
    #                         is_approved = False
    #
    #     if is_approved:
    #         self.date = datetime.now()
    #         self.state = 'done'
    #         self.request_id.budget_request_id = self.id
    #         self.request_id.request_budget_approval()
    #         if msg:
    #             view = self.env.ref('sh_message.sh_message_wizard')
    #             view_id = view and view.id or False
    #             return {
    #                 'name': 'Warning: Budget approved',
    #                 'type': 'ir.actions.act_window',
    #                 'view_type': 'form',
    #                 'view_mode': 'form',
    #                 'res_model': 'sh.message.wizard',
    #                 'views': [(view.id, 'form')],
    #                 'view_id': view.id,
    #                 'target': 'new',
    #                 'context': {'message': msg},
    #             }
    #     else:
    #         msg = '%s\nBudget requested is not approved yet.' % msg
    #         raise UserError(msg)
    #
    # @api.onchange('date')
    # def _onchange_date(self):
    #     for line in self.line_ids:
    #         line.selected_budget_id = False
    #         line.available_budget = False
    #         line.restrict_allow = False
    #
    #         criteria = [('date_from', '<=', self.date), ('date_to', '>=', self.date)]
    #         general_budget_ids = self.env['account.budget.post'].search(
    #             [('account_ids', '=', line.budget_account_id.id)])
    #         budget_ids = []
    #         for general_budget_id in general_budget_ids:
    #             budget_ids.append(general_budget_id.id)
    #         if budget_ids:
    #             criteria.append(('general_budget_id', 'in', budget_ids))
    #         if line['cost_center_id']:
    #             criteria.append(('cost_center_id', '=', line.cost_center_id.id))
    #         if line['analytic_account_id']:
    #             criteria.append(('analytic_account_id', '=', line.analytic_account_id.id))
    #
    #         # appropriate_budget = self.env['crossovered.budget.lines'].sudo().search(criteria, limit=1)
    #         appropriate_budgets = self.env['crossovered.budget.lines'].search(criteria)
    #         for appropriate_budget in appropriate_budgets:
    #             if appropriate_budget.crossovered_budget_id.state == 'validate':
    #                 # line['sequence'] = i
    #                 line.selected_budget_id = appropriate_budget.id
    #                 line.available_budget = -appropriate_budget.avail_req_amount
    #                 line.restrict_allow = appropriate_budget.restrict_allow
    #                 break

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # print('View_id: %s, view_type: %s'%(view_id, view_type))
        res = super(AssetBalanceReport, self).fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type == 'tree':
            # arch = etree.XML(res['arch'])
            # button = arch.xpath("//button[@name='action_budget_to_adjust']")[0]
            # button.set('invisible', self.env.context.get('budget_position') and '0' or '1')
            # setup_modifiers(button)
            # res['arch'] = etree.tostring(arch, encoding='utf-8')
            self.populate_budget_request()
        return res

    @api.multi
    def populate_budget_request(self):
        query = """
            delete from asset_balance_report where create_uid = %s;
            select a.id, a.category_id, a.cost_center_id, a.analytic_account_id, c.account_asset_id, a.date_acq, a.value, a.state,
                sum(d.amount) as total_last_depre,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Jan 2021' and '31 Jan 2021'
                        and move_check = True and move_posted_check = True) as jan,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Feb 2021' and '28 Feb 2021'
                        and move_check = True and move_posted_check = True) as feb,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Mar 2021' and '31 Mar 2021'
                        and move_check = True and move_posted_check = True) as mar,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Apr 2021' and '30 Apr 2021'
                        and move_check = True and move_posted_check = True) as apr,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 May 2021' and '31 May 2021'
                        and move_check = True and move_posted_check = True) as may,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Jun 2021' and '30 Jun 2021'
                        and move_check = True and move_posted_check = True) as jun,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Jul 2021' and '31 Jul 2021'
                        and move_check = True and move_posted_check = True) as jul,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Aug 2021' and '31 Aug 2021'
                        and move_check = True and move_posted_check = True) as aug,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Sep 2021' and '30 Sep 2021'
                        and move_check = True and move_posted_check = True) as sep,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Oct 2021' and '31 Oct 2021'
                        and move_check = True and move_posted_check = True) as oct,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Nov 2021' and '30 Nov 2021'
                        and move_check = True and move_posted_check = True) as nov,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Dec 2021' and '31 Dec 2021'
                        and move_check = True and move_posted_check = True) as dec,
                (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Jan 2021' and '31 Dec 2021'
                        and move_check = True and move_posted_check = True) as this_year_depre,
                (a.value - sum(d.amount) - (select sum(amount) from account_asset_depreciation_line
                 where asset_id = a.id and depreciation_date between '1 Jan 2021' and '31 Dec 2021'
                        and move_check = True and move_posted_check = True)) as book_value,
                a.sale_date, a.disposal_date, a.code
            from account_asset_asset a
                 inner join account_asset_category c on a.category_id = c.id
                 left join account_asset_depreciation_line d on a.id = d.asset_id and d.depreciation_date <= '31 Dec 2020'
            where a.active = true
            group by a.id, a.category_id, a.cost_center_id, a.analytic_account_id, c.account_asset_id, a.date_acq, a.value, a.state
        """
        cr = self.env.cr
        params = (self.env.user.id,)
        cr.execute(query, params)
        res = cr.fetchall()

        for r in res:
            line = self.env['asset.balance.report']
            account_id = r[4] != 'None' and r[4] or False
            if r[5] != 'None' and account_id:
                brl_id = self.env['budget.request.line'].sudo().browse(r[5]).id
                if not brl_id:
                    brl_id = self.env['budget.request.line'].sudo().search([('budget_request_id', '=', r[0]), ('budget_account_id', '=', account_id)]).id
            else:
                brl_id = False
            line.create({
                'asset_id': r[0],
                'category_id': r[1],
                'cost_center_id': r[2] != 'None' and r[2] or False,
                'analytic_account_id': r[3] != 'None' and r[3] or False,
                'account_id': r[4],
                'acquisition_date': r[5],
                'acquisition_amount': r[6],
                'state': r[7],
                'total_last_depre': r[8],
                'jan': r[9],
                'feb': r[10],
                'mar': r[11],
                'apr': r[12],
                'may': r[13],
                'jun': r[14],
                'jul': r[15],
                'aug': r[16],
                'sep': r[17],
                'oct': r[18],
                'nov': r[19],
                'dec': r[20],
                'this_year_depre': r[21],
                'book_value': r[22],
                'sale_date': r[23],
                'disposal_date': r[24],
                'code': r[25]
            })