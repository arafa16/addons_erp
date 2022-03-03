from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class CubeRatioMonth(models.Model):
    _name = "dashboard.cubes.financial.report"
    _description = "Cubes Dashboard Monthly"
    _order = "sequence asc"

    report_id = fields.Many2one('account.financial.report', string="Report")
    name = fields.Char(string="Label")
    sequence = fields.Integer(string="Sequence")
    report_line_id = fields.Many2one('account.financial.report', string="Report Line")
    dimension = fields.Char(string="Description", index=True)
    date = fields.Date(string='Date', index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True, store=True)
    net = fields.Monetary(currency_field='currency_id',)
    balance = fields.Monetary(currency_field='currency_id',)
    company_id = fields.Many2one('res.company', string='Company', required=True,)

    @api.multi
    def populate_analysis(self, report, dimension):
        def save_analysis_yearly():
            line = self.env['dashboard.cubes.yearly']
            if dimension.population_method == 'month':
                bal01 = balance_01
                bal02 = balance_02
                bal03 = balance_03
                bal04 = balance_04
                bal05 = balance_05
                bal06 = balance_06
                bal07 = balance_07
                bal08 = balance_08
                bal09 = balance_09
                bal10 = balance_10
                bal11 = balance_11
                bal12 = balance_12
            else:
                bal01 = month >= 1 and (balance_01 and balance_01 or balance_prev) or 0
                bal02 = month >= 2 and (balance_02 and balance_02 or bal01) or 0
                bal03 = month >= 3 and (balance_03 and balance_03 or bal02) or 0
                bal04 = month >= 4 and (balance_04 and balance_04 or bal03) or 0
                bal05 = month >= 5 and (balance_05 and balance_05 or bal04) or 0
                bal06 = month >= 6 and (balance_06 and balance_06 or bal05) or 0
                bal07 = month >= 7 and (balance_07 and balance_07 or bal06) or 0
                bal08 = month >= 8 and (balance_08 and balance_08 or bal07) or 0
                bal09 = month >= 9 and (balance_09 and balance_09 or bal08) or 0
                bal10 = month >= 10 and (balance_10 and balance_10 or bal09) or 0
                bal11 = month >= 11 and (balance_11 and balance_11 or bal10) or 0
                bal12 = month >= 12 and (balance_12 and balance_12 or bal11) or 0

            line.create({
                'report_id': report.id,
                'name': report.name,
                'sequence': dimension.sequence,
                'report_line_id': dimension.id,
                'dimension': dimension.name,
                'date': date_year,
                'company_id': company_id,
                # 'currency_id': currency_id,
                'balance': balance,
                'balance_01': bal01,
                'balance_02': bal02,
                'balance_03': bal03,
                'balance_04': bal04,
                'balance_05': bal05,
                'balance_06': bal06,
                'balance_07': bal07,
                'balance_08': bal08,
                'balance_09': bal09,
                'balance_10': bal10,
                'balance_11': bal11,
                'balance_12': bal12,
            })

        max_period = datetime.today()
        query = ""
        query += dimension.sequence == 1 and """
                                                delete from dashboard_cubes_financial_report where report_id = %s;
                                                delete from dashboard_cubes_yearly where report_id = %s;
                                            """ % (report.id, report.id) or ""
        query += """
                  select aml.company_id,
                         (date_trunc('MONTH', aml.date) + INTERVAL '1 MONTH - 1 day')::date as date,
                         sum(aml.debit - aml.credit) as net
                  from account_move_line aml
                       inner join account_move am on aml.move_id = am.id
        """
        if dimension.type == 'group':
            query += " inner join account_account a on aml.account_id = a.id "
        query += "where am.state = 'posted' and (aml.debit - aml.credit) != 0 "
        if dimension.type == 'accounts':
            query += " and aml.account_id in (%s) " % ','.join([str(elem) for elem in dimension.account_ids.ids])
        elif dimension.type == 'group':
            query += " and a.group_id in (%s) " % ','.join([str(elem) for elem in dimension.account_group_ids.ids])
        query += """
                 group by aml.company_id, (date_trunc('MONTH', aml.date) + INTERVAL '1 MONTH - 1 day')::date
                 order by aml.company_id, (date_trunc('MONTH', aml.date) + INTERVAL '1 MONTH - 1 day')::date
        """
        cr = self.env.cr
        # params = (','.join([str(elem) for elem in dimension.account_group_ids.ids]))
        cr.execute(query)  # , params)
        res = cr.fetchall()
        first_row = True
        company_id = date_year = False
        population_method = dimension.population_method
        balance = 0
        for r in res:
            if '%s-12-31' % r[1].split('-')[0] != date_year:
                if not first_row:
                    if int(date_year.split('-')[0]) < max_period.year:
                        month = 12
                    elif int(date_year.split('-')[0]) == max_period.year:
                        month = max(month, max_period.month)
                    save_analysis_yearly()
                    balance_prev = balance
                    if r[0] != company_id:
                        yr = int(date_year.split('-')[0])
                        while yr < max_period.year:
                            yr += 1
                            month = yr == max_period.year and max_period.month or 12
                            date_year = '%s-12-31' % yr
                            balance_01 = balance_02 = balance_03 = balance_04 = balance_05 = balance_06 = 0
                            balance_07 = balance_08 = balance_09 = balance_10 = balance_11 = balance_12 = 0
                            save_analysis_yearly()
                else:
                    first_row = False
                if r[0] != company_id:
                    company_id = r[0]
                    balance = balance_prev = 0
                elif dimension.population_method != 'continue':
                    balance = balance_prev = 0
                date_year = '%s-12-31' % r[1].split('-')[0]
                balance_01 = balance_02 = balance_03 = balance_04 = balance_05 = balance_06 = 0
                balance_07 = balance_08 = balance_09 = balance_10 = balance_11 = balance_12 = 0

            net = r[2] * dimension.sign
            if population_method == 'month':
                balance = net
            else:
                balance += net
            date = r[1]
            month = int(date.split('-')[1])
            if month == 1:
                balance_01 = balance
            elif month == 2:
                balance_02 = balance
            elif month == 3:
                balance_03 = balance
            elif month == 4:
                balance_04 = balance
            elif month == 5:
                balance_05 = balance
            elif month == 6:
                balance_06 = balance
            elif month == 7:
                balance_07 = balance
            elif month == 8:
                balance_08 = balance
            elif month == 9:
                balance_09 = balance
            elif month == 10:
                balance_10 = balance
            elif month == 11:
                balance_11 = balance
            elif month == 12:
                balance_12 = balance
            self.save_analysis_monthly(report, dimension, company_id, date, net, balance)
        if company_id and date_year:
            save_analysis_yearly()

    @api.multi
    def get_analysis(self, report, dimension):
        def get_balance_month(mth):
            if mth == 1: return l.balance_01;
            if mth == 2: return l.balance_02;
            if mth == 3: return l.balance_03;
            if mth == 4: return l.balance_04;
            if mth == 5: return l.balance_05;
            if mth == 6: return l.balance_06;
            if mth == 7: return l.balance_07;
            if mth == 8: return l.balance_08;
            if mth == 9: return l.balance_09;
            if mth == 10: return l.balance_10;
            if mth == 11: return l.balance_11;
            if mth == 12: return l.balance_12;

        if dimension.sequence == 1:
            query = """
                        delete from dashboard_cubes_financial_report where report_id = %s;
                        delete from dashboard_cubes_yearly where report_id = %s;
                    """ % (report.id, report.id)
            cr = self.env.cr
            cr.execute(query)
        if not dimension.account_report_id.parent_id.parent_id:
            line_report = dimension.account_report_id.parent_id.name
            report_id = dimension.account_report_id.parent_id.id
        elif not dimension.account_report_id.parent_id.parent_id.parent_id:
            line_report = dimension.account_report_id.parent_id.parent_id.name
        line_sequence = dimension.account_report_id.sequence
        lines = self.env['dashboard.cubes.yearly'].search([
            # ('name', '=', line_report),
            ('report_id', '=', report_id),
            ('sequence', '=', line_sequence)])
        for l in lines:
            for i in range(13):
                if i > 0:
                    date = datetime.strptime(l.date[:4] + '-%s-1' % (i), DF).date() + relativedelta(months=+1, days=-1)
                    val = get_balance_month(i)
                    self.save_analysis_monthly(report, dimension, l.company_id.id, date, val, val)

            ratio = self.env['dashboard.cubes.yearly'].sudo().search([('report_id', '=', report.id),
                                                                      ('sequence', '=', dimension.sequence),
                                                                      ('report_line_id', '=', dimension.id),
                                                                      ('date', '=', l.date),
                                                                      ('company_id', '=', l.company_id.id)])
            if not ratio:
                ratio.create({
                    'report_id': report.id,
                    'name': report.name,
                    'sequence': dimension.sequence,
                    'report_line_id': dimension.id,
                    'dimension': dimension.name,
                    'date': l.date,
                    'company_id': l.company_id.id,
                    'balance': l.balance,
                    'balance_01': l.balance_01,
                    'balance_02': l.balance_02,
                    'balance_03': l.balance_03,
                    'balance_04': l.balance_04,
                    'balance_05': l.balance_05,
                    'balance_06': l.balance_06,
                    'balance_07': l.balance_07,
                    'balance_08': l.balance_08,
                    'balance_09': l.balance_09,
                    'balance_10': l.balance_10,
                    'balance_11': l.balance_11,
                    'balance_12': l.balance_12,
                })
            else:
                ratio.write({
                    'balance': l.balance,
                    'balance_01': l.balance_01,
                    'balance_02': l.balance_02,
                    'balance_03': l.balance_03,
                    'balance_04': l.balance_04,
                    'balance_05': l.balance_05,
                    'balance_06': l.balance_06,
                    'balance_07': l.balance_07,
                    'balance_08': l.balance_08,
                    'balance_09': l.balance_09,
                    'balance_10': l.balance_10,
                    'balance_11': l.balance_11,
                    'balance_12': l.balance_12,
                })

    @api.multi
    def calculate_analysis(self, report, dimension):
        # self.calculate_analysis_monthly(report, dimension)
        self.calculate_analysis_yearly(report, dimension)

    @api.multi
    def save_analysis_monthly(self, report, dimension, company_id, date, net, balance):
        line = self.env['dashboard.cubes.financial.report'].sudo().search([('report_id', '=', report.id),
                                                                           ('sequence', '=', dimension.sequence),
                                                                           ('report_line_id', '=', dimension.id),
                                                                           ('date', '=', date),
                                                                           ('company_id', '=', company_id)])
        if not line:
            line.create({
                'report_id': report.id,
                'name': report.name,
                'sequence': dimension.sequence,
                'report_line_id': dimension.id,
                'dimension': dimension.name,
                'date': date,
                'company_id': company_id,
                'net': net,
                'balance': balance,
            })
        else:
            line.write({
                'net': net,
                'balance': balance,
            })

    @api.multi
    def calculate_analysis_yearly(self, report, dimension):
        def calculate(formula, par1, par2, par3, save_monthly = False, mth = 0):
            if growth_month or k:
                try:
                    val = eval(formula % (par1, par2, par3))
                except:
                    val = par2 != 0 and eval(formula % (par1, par2, par3)) or 0
            else:
                try:
                    val = eval(formula % (par1, par2))
                except:
                    val = par2 != 0 and eval(formula % (par1, par2)) or 0
            if rnd:
                val = round(val)
            if save_monthly:
                date = datetime.strptime(l.date[:4] + '-%s-1' % mth, DF).date() + relativedelta(months=+1, days=-1)
                self.save_analysis_monthly(report, dimension, l.company_id.id, date, val, val)
            return val

        i = j = k = growth_month = formula = rnd = False
        for el in dimension.formula.split(','):
            if not formula:
                formula = el
            elif not i:
                i = int(el)
            elif not j:
                j = int(el)
            else:
                if el == 'M':
                    growth_month = True
                elif el == 'R':
                    rnd = True
                else:
                    # elif isinstance(elem[3], int):
                    k = int(el)
        line_i = self.env['dashboard.cubes.yearly'].search([('report_id', '=', report.id), ('sequence', '=', i)])
        for l in line_i:
            line_j = self.env['dashboard.cubes.yearly'].search([('report_id', '=', report.id),
                                                                ('sequence', '=', j),
                                                                ('company_id', '=', l.company_id.id),
                                                                ('date', '=', l.date)])
            if k:
                line_k = self.env['dashboard.cubes.yearly'].search([('report_id', '=', report.id),
                                                                    ('sequence', '=', k),
                                                                    ('company_id', '=', l.company_id.id),
                                                                    ('date', '=', l.date)])
            if not growth_month:
                n = 1
            else:
                n = (line_j.balance_12 and 12) or (line_j.balance_11 and 11) or (line_j.balance_10 and 11) or \
                    (line_j.balance_09 and 9) or (line_j.balance_08 and 8) or (line_j.balance_07 and 7) or \
                    (line_j.balance_06 and 6) or (line_j.balance_05 and 5) or (line_j.balance_04 and 4) or \
                    (line_j.balance_03 and 3) or (line_j.balance_02 and 2) or (line_j.balance_01 and 1)
            if not k:
                ratio = self.env['dashboard.cubes.yearly'].sudo().search([('report_id', '=', report.id),
                                                                          ('sequence', '=', dimension.sequence),
                                                                          ('report_line_id', '=', dimension.id),
                                                                          ('date', '=', l.date),
                                                                          ('company_id', '=', l.company_id.id)])
                if not ratio:
                    ratio.create({
                        'report_id': report.id,
                        'name': report.name,
                        'sequence': dimension.sequence,
                        'report_line_id': dimension.id,
                        'dimension': dimension.name,
                        'date': l.date,
                        'company_id': l.company_id.id,
                        'balance': calculate(formula, l.balance, line_j.balance, n),
                        'balance_01': calculate(formula, l.balance_01, line_j.balance_01, 1, True, 1),
                        'balance_02': calculate(formula, l.balance_02, line_j.balance_02, 2, True, 2),
                        'balance_03': calculate(formula, l.balance_03, line_j.balance_03, 3, True, 3),
                        'balance_04': calculate(formula, l.balance_04, line_j.balance_04, 4, True, 4),
                        'balance_05': calculate(formula, l.balance_05, line_j.balance_05, 5, True, 5),
                        'balance_06': calculate(formula, l.balance_06, line_j.balance_06, 6, True, 6),
                        'balance_07': calculate(formula, l.balance_07, line_j.balance_07, 7, True, 7),
                        'balance_08': calculate(formula, l.balance_08, line_j.balance_08, 8, True, 8),
                        'balance_09': calculate(formula, l.balance_09, line_j.balance_09, 9, True, 9),
                        'balance_10': calculate(formula, l.balance_10, line_j.balance_10, 10, True, 10),
                        'balance_11': calculate(formula, l.balance_11, line_j.balance_11, 11, True, 11),
                        'balance_12': calculate(formula, l.balance_12, line_j.balance_12, 12, True, 12),
                    })
                else:
                    ratio.write({
                        'balance': calculate(formula, l.balance, line_j.balance, n),
                        'balance_01': calculate(formula, l.balance_01, line_j.balance_01, 1, True, 1),
                        'balance_02': calculate(formula, l.balance_02, line_j.balance_02, 2, True, 2),
                        'balance_03': calculate(formula, l.balance_03, line_j.balance_03, 3, True, 3),
                        'balance_04': calculate(formula, l.balance_04, line_j.balance_04, 4, True, 4),
                        'balance_05': calculate(formula, l.balance_05, line_j.balance_05, 5, True, 5),
                        'balance_06': calculate(formula, l.balance_06, line_j.balance_06, 6, True, 6),
                        'balance_07': calculate(formula, l.balance_07, line_j.balance_07, 7, True, 7),
                        'balance_08': calculate(formula, l.balance_08, line_j.balance_08, 8, True, 8),
                        'balance_09': calculate(formula, l.balance_09, line_j.balance_09, 9, True, 9),
                        'balance_10': calculate(formula, l.balance_10, line_j.balance_10, 10, True, 10),
                        'balance_11': calculate(formula, l.balance_11, line_j.balance_11, 11, True, 11),
                        'balance_12': calculate(formula, l.balance_12, line_j.balance_12, 12, True, 12),
                    })
            else:
                ratio = self.env['dashboard.cubes.yearly'].sudo().search([('report_id', '=', report.id),
                                                                          ('sequence', '=', dimension.sequence),
                                                                          ('report_line_id', '=', dimension.id),
                                                                          ('date', '=', l.date),
                                                                          ('company_id', '=', l.company_id.id)])
                if not ratio:
                    ratio.create({
                        'report_id': report.id,
                        'name': report.name,
                        'sequence': dimension.sequence,
                        'report_line_id': dimension.id,
                        'dimension': dimension.name,
                        'date': l.date,
                        'company_id': l.company_id.id,
                        'balance': calculate(formula, l.balance, line_j.balance, line_k.balance),
                        'balance_01': calculate(formula, l.balance_01, line_j.balance_01, line_k.balance_01, True, 1),
                        'balance_02': calculate(formula, l.balance_02, line_j.balance_02, line_k.balance_02, True, 2),
                        'balance_03': calculate(formula, l.balance_03, line_j.balance_03, line_k.balance_03, True, 3),
                        'balance_04': calculate(formula, l.balance_04, line_j.balance_04, line_k.balance_04, True, 4),
                        'balance_05': calculate(formula, l.balance_05, line_j.balance_05, line_k.balance_05, True, 5),
                        'balance_06': calculate(formula, l.balance_06, line_j.balance_06, line_k.balance_06, True, 6),
                        'balance_07': calculate(formula, l.balance_07, line_j.balance_07, line_k.balance_07, True, 7),
                        'balance_08': calculate(formula, l.balance_08, line_j.balance_08, line_k.balance_08, True, 8),
                        'balance_09': calculate(formula, l.balance_09, line_j.balance_09, line_k.balance_09, True, 9),
                        'balance_10': calculate(formula, l.balance_10, line_j.balance_10, line_k.balance_10, True, 10),
                        'balance_11': calculate(formula, l.balance_11, line_j.balance_11, line_k.balance_11, True, 11),
                        'balance_12': calculate(formula, l.balance_12, line_j.balance_12, line_k.balance_12, True, 12),
                    })
                else:
                    ratio.write({
                        'balance': calculate(formula, l.balance, line_j.balance, line_k.balance),
                        'balance_01': calculate(formula, l.balance_01, line_j.balance_01, line_k.balance_01, True,  1),
                        'balance_02': calculate(formula, l.balance_02, line_j.balance_02, line_k.balance_02, True,  2),
                        'balance_03': calculate(formula, l.balance_03, line_j.balance_03, line_k.balance_03, True,  3),
                        'balance_04': calculate(formula, l.balance_04, line_j.balance_04, line_k.balance_04, True,  4),
                        'balance_05': calculate(formula, l.balance_05, line_j.balance_05, line_k.balance_05, True,  5),
                        'balance_06': calculate(formula, l.balance_06, line_j.balance_06, line_k.balance_06, True,  6),
                        'balance_07': calculate(formula, l.balance_07, line_j.balance_07, line_k.balance_07, True,  7),
                        'balance_08': calculate(formula, l.balance_08, line_j.balance_08, line_k.balance_08, True,  8),
                        'balance_09': calculate(formula, l.balance_09, line_j.balance_09, line_k.balance_09, True,  9),
                        'balance_10': calculate(formula, l.balance_10, line_j.balance_10, line_k.balance_10, True,  10),
                        'balance_11': calculate(formula, l.balance_11, line_j.balance_11, line_k.balance_11, True,  11),
                        'balance_12': calculate(formula, l.balance_12, line_j.balance_12, line_k.balance_12, True,  12),
                    }),


class CubeRatioYear(models.Model):
    _name = "dashboard.cubes.yearly"
    _description = "Cubes Dashboard Yearly"
    _order = "sequence asc"

    report_id = fields.Many2one('account.financial.report', string="Report")
    name = fields.Char(string="Label")
    sequence = fields.Integer(string="Sequence")
    report_line_id = fields.Many2one('account.financial.report', string="Report Line")
    dimension = fields.Char(string="Description", index=True)
    date = fields.Date(string='Date', index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True, store=True)
    balance = fields.Monetary(currency_field='currency_id',)
    balance_01 = fields.Monetary(currency_field='currency_id',string="Jan") # compute='_store_balance_period', store=True
    balance_02 = fields.Monetary(currency_field='currency_id',string="Feb") # compute='_store_balance_period', store=True
    balance_03 = fields.Monetary(currency_field='currency_id',string="Mar") # compute='_store_balance_period', store=True
    balance_04 = fields.Monetary(currency_field='currency_id',string="Apr") # compute='_store_balance_period', store=True
    balance_05 = fields.Monetary(currency_field='currency_id',string="May") # compute='_store_balance_period', store=True
    balance_06 = fields.Monetary(currency_field='currency_id',string="Jun") # compute='_store_balance_period', store=True
    balance_07 = fields.Monetary(currency_field='currency_id',string="Jul") # compute='_store_balance_period', store=True
    balance_08 = fields.Monetary(currency_field='currency_id',string="Aug") # compute='_store_balance_period', store=True
    balance_09 = fields.Monetary(currency_field='currency_id',string="Sep") # compute='_store_balance_period', store=True
    balance_10 = fields.Monetary(currency_field='currency_id',string="Oct") # compute='_store_balance_period', store=True
    balance_11 = fields.Monetary(currency_field='currency_id',string="Nov") # compute='_store_balance_period', store=True
    balance_12 = fields.Monetary(currency_field='currency_id',string="Dec") # compute='_store_balance_period', store=True
    company_id = fields.Many2one('res.company', string='Company', required=True,)


class FinancialReportDashboard(models.Model):
    _name = "account.financial.report.dashboard"
    _description = "Template Report for Dashboard"

    name = fields.Char()
    report_ids = fields.One2many('account.financial.report.dashboard.line', 'dashboard_id', string='Dashboard Line')


class FinancialReportDashboardLine(models.Model):
    _name = "account.financial.report.dashboard.line"
    _description = "Template Report for Dashboard Line"
    _order = "sequence asc"

    name = fields.Char(string="Label")
    sequence = fields.Integer(string="Sequence")
    dashboard_id = fields.Many2one('account.financial.report.dashboard', string='Dashboard')
    report_id = fields.Many2one('account.financial.report', string='Report')


class CubeRatio(models.Model):
    _name="dashboard.cubes.ratio"
    _description="Dashboard Cube Ratio"

    company_id = fields.Many2one('res.company', string='Company', required=True,)
    date = fields.Date(string='Date')
    date_mth = fields.Char(string='Month')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True, store=True)
    current_ratio = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
    quick_ratio = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
    ar_days = fields.Monetary('AR Days', currency_field='currency_id',) # fields.Float(digits=0)
    ap_days = fields.Monetary('AP Days', currency_field='currency_id',) # fields.Float(digits=0)
    inventory_turnover = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=0)
    opr_cycle = fields.Monetary('OPR Cycle', currency_field='currency_id',) # fields.Float(digits=0)
    gp_margin = fields.Monetary('GP Margin (%)', currency_field='currency_id',) # fields.Float(digit=2)
    opr_profit = fields.Monetary('OPR Profit (%)', currency_field='currency_id',) # fields.Float(digit=2)
    der = fields.Monetary('DER', currency_field='currency_id',) # fields.Float(digit=2)
    roa = fields.Monetary('ROA', currency_field='currency_id',) # fields.Float(digit=2)


class CubeRatioTarget(models.Model):
    _name="dashboard.cubes.ratio.target"
    _description="Dashboard Cube Ratio Target"

    company_id = fields.Many2one('res.company', string='Company', required=True,)
    # date = fields.Date(string='Date')
    # date_mth = fields.Char(string='Month')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True, store=True)
    current_ratio = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
    quick_ratio = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
    ar_days = fields.Monetary('AR Days', currency_field='currency_id',) # fields.Float(digits=0)
    ap_days = fields.Monetary('AP Days', currency_field='currency_id',) # fields.Float(digits=0)
    inventory_turnover = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=0)
    opr_cycle = fields.Monetary('OPR Cycle', currency_field='currency_id',) # fields.Float(digits=0)
    gp_margin = fields.Monetary('GP Margin (%)', currency_field='currency_id',) # fields.Float(digit=2)
    opr_profit = fields.Monetary('OPR Profit (%)', currency_field='currency_id',) # fields.Float(digit=2)
    der = fields.Monetary('DER', currency_field='currency_id',) # fields.Float(digit=2)
    roa = fields.Monetary('ROA', currency_field='currency_id',) # fields.Float(digit=2)


# class CubeGPDPP(models.Model):
#     _name="dashboard.cubes.gp.dpp"
#     _description="Dashboard Cube GP DPP"
#
#     company_id = fields.Many2one('res.company', string='Company', required=True,)
#     date = fields.Date(string='Date')
#     date_mth = fields.Char(string='Month')
#     currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True, store=True)
#     labor_supply_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     labor_supply_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     labor_supply_pct = fields.Monetary(currency_field='currency_id',)
#     labor_supply = fields.Char('Labor Supply')
#     job_supply_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     job_supply_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     job_supply_pct = fields.Monetary(currency_field='currency_id',)
#     job_supply = fields.Char('Job Supply')
#     job_supply_2_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     job_supply_2_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     job_supply_2_pct = fields.Monetary(currency_field='currency_id',)
#     job_supply_2 = fields.Char('Job Supply Plant 2')
#     rent_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     rent_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     rent_pct = fields.Monetary(currency_field='currency_id',)
#     rent = fields.Char('Rent')
#     pb_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     pb_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     pb_pct = fields.Monetary(currency_field='currency_id',)
#     pb = fields.Char('PB/Component')
#     total_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_pct = fields.Monetary(currency_field='currency_id',)
#     total = fields.Char('Keseluruhan')
#
#
# class CubeGPGSI(models.Model):
#     _name="dashboard.cubes.gp.gsi"
#     _description="Dashboard Cube GP GSI"
#
#     company_id = fields.Many2one('res.company', string='Company', required=True,)
#     date = fields.Date(string='Date')
#     date_mth = fields.Char(string='Month')
#     currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True, store=True)
#     it_officer_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     it_officer_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     it_officer_pct = fields.Monetary(currency_field='currency_id',)
#     it_officer = fields.Char('IT Officer')
#     administration_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     administration_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     administration_pct = fields.Monetary(currency_field='currency_id',)
#     administration = fields.Char('Administration')
#     safety_officer_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     safety_officer_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     safety_officer_pct = fields.Monetary(currency_field='currency_id',)
#     safety_officer = fields.Char('Safety Officer')
#     venue_management_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     venue_management_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     venue_management_pct = fields.Monetary(currency_field='currency_id',)
#     venue_management = fields.Char('Venue Management')
#     solution_management_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     solution_management_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     solution_management_pct = fields.Monetary(currency_field='currency_id',)
#     solution_management = fields.Char('Solution Management')
#     total_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_pct = fields.Monetary(currency_field='currency_id',)
#     total = fields.Char('Keseluruhan')
#
#
# class CubeGPYKBUT(models.Model):
#     _name="dashboard.cubes.gp.ykbut"
#     _description="Dashboard Cube GP YKBUT"
#
#     company_id = fields.Many2one('res.company', string='Company', required=True,)
#     date = fields.Date(string='Date')
#     date_mth = fields.Char(string='Month')
#     currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True, store=True)
#     ut_school_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     ut_school_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     ut_school_pct = fields.Monetary(currency_field='currency_id',)
#     ut_school = fields.Char('UT School')
#     daycare_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     daycare_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     daycare_pct = fields.Monetary(currency_field='currency_id',)
#     daycare = fields.Char('Daycare')
#     poliklinik_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     poliklinik_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     poliklinik_pct = fields.Monetary(currency_field='currency_id',)
#     poliklinik = fields.Char('Poliklinik')
#     total_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_pct = fields.Monetary(currency_field='currency_id',)
#     total = fields.Char('Yayasan (Rekap)')
#
#
# class CubeGPLSPABI(models.Model):
#     _name="dashboard.cubes.gp.lspabi"
#     _description="Dashboard Cube GP LSPABI"
#
#     company_id = fields.Many2one('res.company', string='Company', required=True,)
#     date = fields.Date(string='Date')
#     date_mth = fields.Char(string='Month')
#     currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True, store=True)
#     ser_kom_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     ser_kom_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     ser_kom_pct = fields.Monetary(currency_field='currency_id',)
#     ser_kom = fields.Char('Sertifikasi Kompetensi')
#     ser_kom_ext_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     ser_kom_ext_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     ser_kom_ext_pct = fields.Monetary(currency_field='currency_id',)
#     ser_kom_ext = fields.Char('Perpanjangan (RCC) Sertifikat')
#     other_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     other_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     other_pct = fields.Monetary(currency_field='currency_id',)
#     other = fields.Char('Pendapatan Lain-lain')
#     total_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_pct = fields.Monetary(currency_field='currency_id',)
#     total = fields.Char('Keseluruhan')
#
#
# class CubeGPMBUT(models.Model):
#     _name="dashboard.cubes.gp.mbut"
#     _description="Dashboard Cube GP MBUT"
#
#     company_id = fields.Many2one('res.company', string='Company', required=True,)
#     date = fields.Date(string='Date')
#     date_mth = fields.Char(string='Month')
#     currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True, store=True)
#
#     civ_cons_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     civ_cons_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     civ_cons_pct = fields.Monetary(currency_field='currency_id',)
#     civ_cons = fields.Char('Civil Construction')
#
#     maint_ac_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     maint_ac_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     maint_ac_pct = fields.Monetary(currency_field='currency_id',)
#     maint_ac = fields.Char('Maintenance AC')
#
#     maint_gd_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     maint_gd_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     maint_gd_pct = fields.Monetary(currency_field='currency_id',)
#     maint_gd = fields.Char('Maintenance Gedung')
#
#     maint_stp_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     maint_stp_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     maint_stp_pct = fields.Monetary(currency_field='currency_id',)
#     maint_stp = fields.Char('Maintenance STP - GWT')
#
#     rent_car_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     rent_car_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     rent_car_pct = fields.Monetary(currency_field='currency_id',)
#     rent_car = fields.Char('Rent a Car')
#
#     admin_supp_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     admin_supp_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     admin_supp_pct = fields.Monetary(currency_field='currency_id',)
#     admin_supp = fields.Char('Administration Support')
#
#     cleaning_svc_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     cleaning_svc_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     cleaning_svc_pct = fields.Monetary(currency_field='currency_id',)
#     cleaning_svc = fields.Char('Cleaning Service')
#
#     job_supp_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     job_supp_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     job_supp_pct = fields.Monetary(currency_field='currency_id',)
#     job_supp = fields.Char('Job Supply')
#
#     ob_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     ob_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     ob_pct = fields.Monetary(currency_field='currency_id',)
#     ob = fields.Char('Office Boy')
#
#     svc_japek_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     svc_japek_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     svc_japek_pct = fields.Monetary(currency_field='currency_id',)
#     svc_japek = fields.Char('Services Japek')
#
#     me_japek_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     me_japek_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     me_japek_pct = fields.Monetary(currency_field='currency_id',)
#     me_japek = fields.Char('ME Japek')
#
#     total_revenue = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_gp = fields.Monetary(currency_field='currency_id',) # fields.Float(digits=2)
#     total_pct = fields.Monetary(currency_field='currency_id',)
#     total = fields.Char('Keseluruhan')

