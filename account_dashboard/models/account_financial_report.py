# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from datetime import datetime

# ---------------------------------------------------------
# Account Financial Report
# ---------------------------------------------------------


class account_financial_report(models.Model):
    _inherit = "account.financial.report"

    @api.one
    def _get_parent_isdashboard(self):
        if not self.parent_id.parent_id:
            self.for_dashboard_only = self.parent_id.dashboard
        elif not self.parent_id.parent_id.parent_id:
            self.for_dashboard_only = self.parent_id.parent_id.dashboard

    dashboard = fields.Boolean(string='Show on Dashboard', default=False)
    type = fields.Selection(selection_add=[('group', 'Account Groups'), ('formula', 'Formula'),])
    formula = fields.Char(invisble=[(type, '!=', 'formula')])
    for_dashboard_only = fields.Boolean(compute='_get_parent_isdashboard')
    population_method = fields.Selection([
        ('month', 'Monthly (reset every month)'),
        ('year', 'Monthly (reset every year)'),
        ('continue', 'Monthly (no reset)'),
    ], string='Data Population Method', default='continue')
    account_group_ids = fields.Many2many('account.group', 'account_account_financial_account_group', 'account_group_id', 'type_id', 'Account Groups')

    @api.multi
    def populate_cube(self):
        for report in self:
            if report.dashboard:
                for line in self.env['account.financial.report'].search([('parent_id', '=', report.id)], order="sequence asc"):
                    if line.type == 'group' and line.account_group_ids or line.type == 'accounts' and line.account_ids:
                        cube = self.env['dashboard.cubes.financial.report']
                        cube.populate_analysis(report, line)
                    elif line.type == 'account_report' and line.account_report_id:
                        cube = self.env['dashboard.cubes.financial.report']
                        cube.get_analysis(report, line)
                    elif line.type == 'formula' and line.formula:
                        cube = self.env['dashboard.cubes.financial.report']
                        cube.calculate_analysis(report, line)

    @api.multi
    def populate_cubes(self):
        for report in self.env['account.financial.report'].search([('dashboard', '=', True)], order="id asc"):
            report.populate_cube()
        self.populate_cube_ratio()
        # self.populate_cube_gp_dpp()
        # self.populate_cube_gp_gsi()
        # self.populate_cube_gp_ykbut()
        # self.populate_cube_gp_lspabi()
        # self.populate_cube_gp_mbut()

    @api.multi
    def populate_cube_ratio(self):
        query_report = """ 
            SELECT l.report_id
            FROM account_financial_report_dashboard d
                 INNER JOIN account_financial_report_dashboard_line l on d.id = l.dashboard_id
            WHERE d.name = 'Rasio - Rasio'
            ORDER BY l.id
        """
        cr = self.env.cr
        cr.execute(query_report)  # , params)
        reports = cr.fetchall()
        report_ids = []
        for r in reports:
            report_ids.append(r[0])

        query_period = """
            DELETE FROM dashboard_cubes_ratio;
            SELECT DISTINCT company_id, date
            FROM dashboard_cubes_financial_report
            ORDER BY company_id, date
        """
        cr = self.env.cr
        cr.execute(query_period)  # , params)
        res = cr.fetchall()
        for r in res:
            company_id = r[0]
            date = r[1]
            date_mth = datetime.strptime(date, '%Y-%m-%d').strftime("%B-%Y")
            current_ratio = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[0])])
            quick_ratio = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[1])])
            ar_days = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[2])])
            ap_days = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[3])])
            inventory_turnover = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[4])])
            opr_cycle = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[5])])
            gp_margin = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[6])])
            opr_profit = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[7])])
            der = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[8])])
            roa = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[9])])
            ratio = self.env['dashboard.cubes.ratio']
            ratio.create({
                'company_id': company_id,
                'date': date,
                'date_mth': date_mth,
                'current_ratio': current_ratio.balance,
                'quick_ratio': quick_ratio.balance,
                'ar_days': ar_days.balance,
                'ap_days': ap_days.balance,
                'inventory_turnover': inventory_turnover.balance,
                'opr_cycle': opr_cycle.balance,
                'gp_margin': gp_margin.balance,
                'opr_profit': opr_profit.balance,
                'der': der.balance,
                'roa': roa.balance,
            })

    # @api.multi
    # def populate_cube_gp_dpp(self):
    #     query_report = """
    #         SELECT l.report_id
    #         FROM account_financial_report_dashboard d
    #              INNER JOIN account_financial_report_dashboard_line l on d.id = l.dashboard_id
    #         WHERE d.name = 'GP by Segment - DPP'
    #         ORDER BY l.sequence ASC
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_report)  # , params)
    #     reports = cr.fetchall()
    #     report_ids = []
    #     for r in reports:
    #         report_ids.append(r[0])
    #
    #     query_period = """
    #         DELETE FROM dashboard_cubes_gp_dpp;
    #         SELECT DISTINCT company_id, date
    #         FROM dashboard_cubes_financial_report
    #         WHERE company_id = 5
    #         ORDER BY date
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_period)  # , params)
    #     res = cr.fetchall()
    #     for r in res:
    #         company_id = r[0]
    #         date = r[1]
    #         date_mth = datetime.strptime(date, '%Y-%m-%d').strftime("%B-%Y")
    #         labor_supply_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[0])])
    #         labor_supply_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[1])])
    #         job_supply_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[2])])
    #         job_supply_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[3])])
    #         job_supply_2_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[4])])
    #         job_supply_2_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[5])])
    #         rent_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[6])])
    #         rent_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[7])])
    #         pb_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[8])])
    #         pb_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[9])])
    #
    #         labor_supply_revenue_bal = labor_supply_revenue.report_line_id.population_method == 'month' and labor_supply_revenue.net or labor_supply_revenue.balance
    #         labor_supply_gp_bal = labor_supply_gp.report_line_id.population_method == 'month' and labor_supply_gp.net or labor_supply_gp.balance
    #         labor_supply_pct = labor_supply_revenue_bal and labor_supply_gp_bal / labor_supply_revenue_bal or 0
    #
    #         job_supply_revenue_bal = job_supply_revenue.report_line_id.population_method == 'month' and job_supply_revenue.net or job_supply_revenue.balance
    #         job_supply_gp_bal = job_supply_gp.report_line_id.population_method == 'month' and job_supply_gp.net or job_supply_gp.balance
    #         job_supply_pct = job_supply_revenue_bal and job_supply_gp_bal / job_supply_revenue_bal or 0
    #
    #         job_supply_2_revenue_bal = job_supply_2_revenue.report_line_id.population_method == 'month' and job_supply_2_revenue.net or job_supply_2_revenue.balance
    #         job_supply_2_gp_bal = job_supply_2_gp.report_line_id.population_method == 'month' and job_supply_2_gp.net or job_supply_2_gp.balance
    #         job_supply_2_pct = job_supply_2_revenue_bal and job_supply_2_gp_bal / job_supply_2_revenue_bal or 0
    #
    #         rent_revenue_bal = rent_revenue.report_line_id.population_method == 'month' and rent_revenue.net or rent_revenue.balance
    #         rent_gp_bal = rent_gp.report_line_id.population_method == 'month' and rent_gp.net or rent_gp.balance
    #         rent_pct = rent_revenue_bal and rent_gp_bal / rent_revenue_bal or 0
    #
    #         pb_revenue_bal = pb_revenue.report_line_id.population_method == 'month' and pb_revenue.net or pb_revenue.balance
    #         pb_gp_bal = pb_gp.report_line_id.population_method == 'month' and pb_gp.net or pb_gp.balance
    #         pb_pct = pb_revenue_bal and pb_gp_bal / pb_revenue_bal or 0
    #
    #         total_revenue = labor_supply_revenue_bal + job_supply_revenue_bal + rent_revenue_bal + pb_revenue_bal + job_supply_2_revenue_bal
    #         total_gp = labor_supply_gp_bal + job_supply_gp_bal + rent_gp_bal + pb_gp_bal + job_supply_2_gp_bal
    #         total_pct = total_revenue and total_gp / total_revenue or 0
    #
    #         ratio = self.env['dashboard.cubes.gp.dpp']
    #         ratio.create({
    #             'company_id': company_id,
    #             'date': date,
    #             'date_mth': date_mth,
    #             'labor_supply_revenue': labor_supply_revenue_bal,
    #             'labor_supply_gp': labor_supply_gp_bal,
    #             'labor_supply_pct': labor_supply_pct,
    #             'labor_supply': '%s:%s' % ('{:,.0f}'.format(labor_supply_gp_bal), '{:,.2%}'.format(labor_supply_pct)),
    #             'job_supply_revenue': job_supply_revenue_bal,
    #             'job_supply_gp': job_supply_gp_bal,
    #             'job_supply_pct': job_supply_pct,
    #             'job_supply': '%s:%s' % ('{:,.0f}'.format(job_supply_gp_bal), '{:,.2%}'.format(job_supply_pct)),
    #             'job_supply_2_revenue': job_supply_2_revenue_bal,
    #             'job_supply_2_gp': job_supply_2_gp_bal,
    #             'job_supply_2_pct': job_supply_2_pct,
    #             'job_supply_2': '%s:%s' % ('{:,.0f}'.format(job_supply_2_gp_bal), '{:,.2%}'.format(job_supply_2_pct)),
    #             'rent_revenue': rent_revenue_bal,
    #             'rent_gp': rent_gp_bal,
    #             'rent_pct': rent_pct,
    #             'rent': '%s:%s' % ('{:,.0f}'.format(rent_gp_bal), '{:,.2%}'.format(rent_pct)),
    #             'pb_revenue': pb_revenue_bal,
    #             'pb_gp': pb_gp_bal,
    #             'pb_pct': pb_pct,
    #             'pb': '%s:%s' % ('{:,.0f}'.format(pb_gp_bal), '{:,.2%}'.format(pb_pct)),
    #             'total_revenue': total_revenue,
    #             'total_gp': total_gp,
    #             'total_pct': total_pct,
    #             'total': '%s:%s' % ('{:,.0f}'.format(total_gp), '{:,.2%}'.format(total_pct)),
    #         })
    #
    # @api.multi
    # def populate_cube_gp_gsi(self):
    #     query_report = """
    #         SELECT l.report_id
    #         FROM account_financial_report_dashboard d
    #              INNER JOIN account_financial_report_dashboard_line l on d.id = l.dashboard_id
    #         WHERE d.name = 'GP by Segment - GSI'
    #         ORDER BY l.sequence ASC
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_report)  # , params)
    #     reports = cr.fetchall()
    #     report_ids = []
    #     for r in reports:
    #         report_ids.append(r[0])
    #
    #     query_period = """
    #         DELETE FROM dashboard_cubes_gp_gsi;
    #         SELECT DISTINCT company_id, date
    #         FROM dashboard_cubes_financial_report
    #         WHERE company_id = 6
    #         ORDER BY date
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_period)  # , params)
    #     res = cr.fetchall()
    #     for r in res:
    #         company_id = r[0]
    #         date = r[1]
    #         date_mth = datetime.strptime(date, '%Y-%m-%d').strftime("%B-%Y")
    #         it_officer_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[0])])
    #         it_officer_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[1])])
    #         administration_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[2])])
    #         administration_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[3])])
    #         safety_officer_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[4])])
    #         safety_officer_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[5])])
    #         venue_management_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[6])])
    #         venue_management_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[7])])
    #         solution_management_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[8])])
    #         solution_management_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[9])])
    #
    #         it_officer_revenue_bal = it_officer_revenue.report_line_id.population_method == 'month' and it_officer_revenue.net or it_officer_revenue.balance
    #         it_officer_gp_bal = it_officer_gp.report_line_id.population_method == 'month' and it_officer_gp.net or it_officer_gp.balance
    #         it_officer_pct = it_officer_revenue_bal and it_officer_gp_bal / it_officer_revenue_bal or 0
    #
    #         administration_revenue_bal = administration_revenue.report_line_id.population_method == 'month' and administration_revenue.net or administration_revenue.balance
    #         administration_gp_bal = administration_gp.report_line_id.population_method == 'month' and administration_gp.net or administration_gp.balance
    #         administration_pct = administration_revenue_bal and administration_gp_bal / administration_revenue_bal or 0
    #
    #         safety_officer_revenue_bal = safety_officer_revenue.report_line_id.population_method == 'month' and safety_officer_revenue.net or safety_officer_revenue.balance
    #         safety_officer_gp_bal = safety_officer_gp.report_line_id.population_method == 'month' and safety_officer_gp.net or safety_officer_gp.balance
    #         safety_officer_pct = safety_officer_revenue_bal and safety_officer_gp_bal / safety_officer_revenue_bal or 0
    #
    #         venue_management_revenue_bal = venue_management_revenue.report_line_id.population_method == 'month' and venue_management_revenue.net or venue_management_revenue.balance
    #         venue_management_gp_bal = venue_management_gp.report_line_id.population_method == 'month' and venue_management_gp.net or venue_management_gp.balance
    #         venue_management_pct = venue_management_revenue_bal and venue_management_gp_bal / venue_management_revenue_bal or 0
    #
    #         solution_management_revenue_bal = solution_management_revenue.report_line_id.population_method == 'month' and solution_management_revenue.net or solution_management_revenue.balance
    #         solution_management_gp_bal = solution_management_gp.report_line_id.population_method == 'month' and solution_management_gp.net or solution_management_gp.balance
    #         solution_management_pct = solution_management_revenue_bal and solution_management_gp_bal / solution_management_revenue_bal or 0
    #
    #         total_revenue = it_officer_revenue_bal + administration_revenue_bal + safety_officer_revenue_bal + venue_management_revenue_bal + solution_management_revenue_bal
    #         total_gp = it_officer_gp_bal + administration_gp_bal + safety_officer_gp_bal + venue_management_gp_bal + solution_management_gp_bal
    #         total_pct = total_revenue and total_gp / total_revenue or 0
    #
    #         ratio = self.env['dashboard.cubes.gp.gsi']
    #         ratio.create({
    #             'company_id': company_id,
    #             'date': date,
    #             'date_mth': date_mth,
    #             'it_officer_revenue': it_officer_revenue_bal,
    #             'it_officer_gp': it_officer_gp_bal,
    #             'it_officer_pct': it_officer_pct,
    #             'it_officer': '%s:%s' % ('{:,.0f}'.format(it_officer_gp_bal), '{:,.2%}'.format(it_officer_pct)),
    #             'administration_revenue': administration_revenue_bal,
    #             'administration_gp': administration_gp_bal,
    #             'administration_pct': administration_pct,
    #             'administration': '%s:%s' % ('{:,.0f}'.format(administration_gp_bal), '{:,.2%}'.format(administration_pct)),
    #             'safety_officer_revenue': safety_officer_revenue_bal,
    #             'safety_officer_gp': safety_officer_gp_bal,
    #             'safety_officer_pct': safety_officer_pct,
    #             'safety_officer': '%s:%s' % ('{:,.0f}'.format(safety_officer_gp_bal), '{:,.2%}'.format(safety_officer_pct)),
    #             'venue_management_revenue': venue_management_revenue_bal,
    #             'venue_management_gp': venue_management_gp_bal,
    #             'venue_management_pct': venue_management_pct,
    #             'venue_management': '%s:%s' % ('{:,.0f}'.format(venue_management_gp_bal), '{:,.2%}'.format(venue_management_pct)),
    #             'solution_management_revenue': solution_management_revenue_bal,
    #             'solution_management_gp': solution_management_gp_bal,
    #             'solution_management_pct': solution_management_pct,
    #             'solution_management': '%s:%s' % ('{:,.0f}'.format(solution_management_gp_bal), '{:,.2%}'.format(solution_management_pct)),
    #             'total_revenue': total_revenue,
    #             'total_gp': total_gp,
    #             'total_pct': total_pct,
    #             'total': '%s:%s' % ('{:,.0f}'.format(total_gp), '{:,.2%}'.format(total_pct)),
    #         })
    #
    # @api.multi
    # def populate_cube_gp_ykbut(self):
    #     query_report = """
    #         SELECT l.report_id
    #         FROM account_financial_report_dashboard d
    #              INNER JOIN account_financial_report_dashboard_line l on d.id = l.dashboard_id
    #         WHERE d.name = 'GP by Segment - YKBUT'
    #         ORDER BY l.sequence ASC
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_report)  # , params)
    #     reports = cr.fetchall()
    #     report_ids = []
    #     for r in reports:
    #         report_ids.append(r[0])
    #
    #     query_period = """
    #         DELETE FROM dashboard_cubes_gp_ykbut;
    #         SELECT DISTINCT company_id, date
    #         FROM dashboard_cubes_financial_report
    #         WHERE company_id = 4
    #         ORDER BY date
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_period)  # , params)
    #     res = cr.fetchall()
    #     for r in res:
    #         company_id = r[0]
    #         date = r[1]
    #         date_mth = datetime.strptime(date, '%Y-%m-%d').strftime("%B-%Y")
    #         ut_school_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[0])])
    #         ut_school_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[1])])
    #         daycare_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[2])])
    #         daycare_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[3])])
    #         poliklinik_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[4])])
    #         poliklinik_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[5])])
    #
    #         ut_school_revenue_bal = ut_school_revenue.report_line_id.population_method == 'month' and ut_school_revenue.net or ut_school_revenue.balance
    #         ut_school_gp_bal = ut_school_gp.report_line_id.population_method == 'month' and ut_school_gp.net or ut_school_gp.balance
    #         ut_school_pct = ut_school_revenue_bal and ut_school_gp_bal / ut_school_revenue_bal or 0
    #
    #         daycare_revenue_bal = daycare_revenue.report_line_id.population_method == 'month' and daycare_revenue.net or daycare_revenue.balance
    #         daycare_gp_bal = daycare_gp.report_line_id.population_method == 'month' and daycare_gp.net or daycare_gp.balance
    #         daycare_pct = daycare_revenue_bal and daycare_gp_bal / daycare_revenue_bal or 0
    #
    #         poliklinik_revenue_bal = poliklinik_revenue.report_line_id.population_method == 'month' and poliklinik_revenue.net or poliklinik_revenue.balance
    #         poliklinik_gp_bal = poliklinik_gp.report_line_id.population_method == 'month' and poliklinik_gp.net or poliklinik_gp.balance
    #         poliklinik_pct = poliklinik_revenue_bal and poliklinik_gp_bal / poliklinik_revenue_bal or 0
    #
    #         total_revenue = ut_school_revenue_bal + daycare_revenue_bal + poliklinik_revenue_bal
    #         total_gp = ut_school_gp_bal + daycare_gp_bal + poliklinik_gp_bal
    #         total_pct = total_revenue and total_gp / total_revenue or 0
    #
    #         ratio = self.env['dashboard.cubes.gp.ykbut']
    #         ratio.create({
    #             'company_id': company_id,
    #             'date': date,
    #             'date_mth': date_mth,
    #             'ut_school_revenue': ut_school_revenue_bal,
    #             'ut_school_gp': ut_school_gp_bal,
    #             'ut_school_pct': ut_school_pct,
    #             'ut_school': '%s:%s' % ('{:,.0f}'.format(ut_school_gp_bal), '{:,.2%}'.format(ut_school_pct)),
    #             'daycare_revenue': daycare_revenue_bal,
    #             'daycare_gp': daycare_gp_bal,
    #             'daycare_pct': daycare_pct,
    #             'daycare': '%s:%s' % ('{:,.0f}'.format(daycare_gp_bal), '{:,.2%}'.format(daycare_pct)),
    #             'poliklinik_revenue': poliklinik_revenue_bal,
    #             'poliklinik_gp': poliklinik_gp_bal,
    #             'poliklinik_pct': poliklinik_pct,
    #             'poliklinik': '%s:%s' % ('{:,.0f}'.format(poliklinik_gp_bal), '{:,.2%}'.format(poliklinik_pct)),
    #             'total_revenue': total_revenue,
    #             'total_gp': total_gp,
    #             'total_pct': total_pct,
    #             'total': '%s:%s' % ('{:,.0f}'.format(total_gp), '{:,.2%}'.format(total_pct)),
    #         })
    #
    # @api.multi
    # def populate_cube_gp_lspabi(self):
    #     query_report = """
    #         SELECT l.report_id
    #         FROM account_financial_report_dashboard d
    #              INNER JOIN account_financial_report_dashboard_line l on d.id = l.dashboard_id
    #         WHERE d.name = 'GP by Segment - LSPABI'
    #         ORDER BY l.sequence ASC
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_report)  # , params)
    #     reports = cr.fetchall()
    #     report_ids = []
    #     for r in reports:
    #         report_ids.append(r[0])
    #
    #     query_period = """
    #         DELETE FROM dashboard_cubes_gp_lspabi;
    #         SELECT DISTINCT company_id, date
    #         FROM dashboard_cubes_financial_report
    #         WHERE company_id = 7
    #         ORDER BY date
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_period)  # , params)
    #     res = cr.fetchall()
    #     for r in res:
    #         company_id = r[0]
    #         date = r[1]
    #         date_mth = datetime.strptime(date, '%Y-%m-%d').strftime("%B-%Y")
    #         ser_kom_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[0])])
    #         ser_kom_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[1])])
    #         ser_kom_ext_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[2])])
    #         ser_kom_ext_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[3])])
    #         other_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[4])])
    #         other_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[5])])
    #
    #         ser_kom_revenue_bal = ser_kom_revenue.report_line_id.population_method == 'month' and ser_kom_revenue.net or ser_kom_revenue.balance
    #         ser_kom_gp_bal = ser_kom_gp.report_line_id.population_method == 'month' and ser_kom_gp.net or ser_kom_gp.balance
    #         ser_kom_pct = ser_kom_revenue_bal and ser_kom_gp_bal / ser_kom_revenue_bal or 0
    #
    #         ser_kom_ext_revenue_bal = ser_kom_ext_revenue.report_line_id.population_method == 'month' and ser_kom_ext_revenue.net or ser_kom_ext_revenue.balance
    #         ser_kom_ext_gp_bal = ser_kom_ext_gp.report_line_id.population_method == 'month' and ser_kom_ext_gp.net or ser_kom_ext_gp.balance
    #         ser_kom_ext_pct = ser_kom_ext_revenue_bal and ser_kom_ext_gp_bal / ser_kom_ext_revenue_bal or 0
    #
    #         other_revenue_bal = other_revenue.report_line_id.population_method == 'month' and other_revenue.net or other_revenue.balance
    #         other_gp_bal = other_gp.report_line_id.population_method == 'month' and other_gp.net or other_gp.balance
    #         other_pct = other_revenue_bal and other_gp_bal / other_revenue_bal or 0
    #
    #         total_revenue = ser_kom_revenue_bal + ser_kom_ext_revenue_bal + other_revenue_bal
    #         total_gp = ser_kom_gp_bal + ser_kom_ext_gp_bal + other_gp_bal
    #         total_pct = total_revenue and total_gp / total_revenue or 0
    #
    #         ratio = self.env['dashboard.cubes.gp.lspabi']
    #         ratio.create({
    #             'company_id': company_id,
    #             'date': date,
    #             'date_mth': date_mth,
    #             'ser_kom_revenue': ser_kom_revenue_bal,
    #             'ser_kom_gp': ser_kom_gp_bal,
    #             'ser_kom_pct': ser_kom_pct,
    #             'ser_kom': '%s:%s' % ('{:,.0f}'.format(ser_kom_gp_bal), '{:,.2%}'.format(ser_kom_pct)),
    #             'ser_kom_ext_revenue': ser_kom_ext_revenue_bal,
    #             'ser_kom_ext_gp': ser_kom_ext_gp_bal,
    #             'ser_kom_ext_pct': ser_kom_ext_pct,
    #             'ser_kom_ext': '%s:%s' % ('{:,.0f}'.format(ser_kom_ext_gp_bal), '{:,.2%}'.format(ser_kom_ext_pct)),
    #             'other_revenue': other_revenue_bal,
    #             'other_gp': other_gp_bal,
    #             'other_pct': other_pct,
    #             'other': '%s:%s' % ('{:,.0f}'.format(other_gp_bal), '{:,.2%}'.format(other_pct)),
    #             'total_revenue': total_revenue,
    #             'total_gp': total_gp,
    #             'total_pct': total_pct,
    #             'total': '%s:%s' % ('{:,.0f}'.format(total_gp), '{:,.2%}'.format(total_pct)),
    #         })
    #
    # @api.multi
    # def populate_cube_gp_mbut(self):
    #     query_report = """
    #         SELECT l.report_id
    #         FROM account_financial_report_dashboard d
    #              INNER JOIN account_financial_report_dashboard_line l on d.id = l.dashboard_id
    #         WHERE d.name = 'GP by Segment - MBUT'
    #         ORDER BY l.sequence ASC
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_report)  # , params)
    #     reports = cr.fetchall()
    #     report_ids = []
    #     for r in reports:
    #         report_ids.append(r[0])
    #
    #     query_period = """
    #         DELETE FROM dashboard_cubes_gp_mbut;
    #         SELECT DISTINCT company_id, date
    #         FROM dashboard_cubes_financial_report
    #         WHERE company_id = 8
    #         ORDER BY date
    #     """
    #     cr = self.env.cr
    #     cr.execute(query_period)  # , params)
    #     res = cr.fetchall()
    #     for r in res:
    #         company_id = r[0]
    #         date = r[1]
    #         date_mth = datetime.strptime(date, '%Y-%m-%d').strftime("%B-%Y")
    #
    #         civ_cons_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[0])])
    #         civ_cons_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[1])])
    #
    #         maint_ac_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[2])])
    #         maint_ac_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[3])])
    #
    #         maint_gd_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[4])])
    #         maint_gd_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[5])])
    #
    #         maint_stp_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[6])])
    #         maint_stp_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[7])])
    #
    #         rent_car_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[8])])
    #         rent_car_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[9])])
    #
    #         admin_supp_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[10])])
    #         admin_supp_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[11])])
    #
    #         cleaning_svc_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[12])])
    #         cleaning_svc_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[13])])
    #
    #         job_supp_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[14])])
    #         job_supp_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[15])])
    #
    #         ob_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[16])])
    #         ob_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[17])])
    #
    #         svc_japek_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[18])])
    #         svc_japek_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[19])])
    #
    #         me_japek_revenue = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[20])])
    #         me_japek_gp = self.env['dashboard.cubes.financial.report'].sudo().search([('company_id', '=', company_id), ('date', '=', date), ('report_line_id', '=', report_ids[21])])
    #
    #         civ_cons_revenue_bal = civ_cons_revenue.report_line_id.population_method == 'month' and civ_cons_revenue.net or civ_cons_revenue.balance
    #         civ_cons_gp_bal = civ_cons_gp.report_line_id.population_method == 'month' and civ_cons_gp.net or civ_cons_gp.balance
    #         civ_cons_pct = civ_cons_revenue_bal and civ_cons_gp_bal / civ_cons_revenue_bal or 0
    #
    #         maint_ac_revenue_bal = maint_ac_revenue.report_line_id.population_method == 'month' and maint_ac_revenue.net or maint_ac_revenue.balance
    #         maint_ac_gp_bal = maint_ac_gp.report_line_id.population_method == 'month' and maint_ac_gp.net or maint_ac_gp.balance
    #         maint_ac_pct = maint_ac_revenue_bal and maint_ac_gp_bal / maint_ac_revenue_bal or 0
    #
    #         maint_gd_revenue_bal = maint_gd_revenue.report_line_id.population_method == 'month' and maint_gd_revenue.net or maint_gd_revenue.balance
    #         maint_gd_gp_bal = maint_gd_gp.report_line_id.population_method == 'month' and maint_gd_gp.net or maint_gd_gp.balance
    #         maint_gd_pct = maint_gd_revenue_bal and maint_gd_gp_bal / maint_gd_revenue_bal or 0
    #
    #         maint_stp_revenue_bal = maint_stp_revenue.report_line_id.population_method == 'month' and maint_stp_revenue.net or maint_stp_revenue.balance
    #         maint_stp_gp_bal = maint_stp_gp.report_line_id.population_method == 'month' and maint_stp_gp.net or maint_stp_gp.balance
    #         maint_stp_pct = maint_stp_revenue_bal and maint_stp_gp_bal / maint_stp_revenue_bal or 0
    #
    #         rent_car_revenue_bal = rent_car_revenue.report_line_id.population_method == 'month' and rent_car_revenue.net or rent_car_revenue.balance
    #         rent_car_gp_bal = rent_car_gp.report_line_id.population_method == 'month' and rent_car_gp.net or rent_car_gp.balance
    #         rent_car_pct = rent_car_revenue_bal and rent_car_gp_bal / rent_car_revenue_bal or 0
    #
    #         admin_supp_revenue_bal = admin_supp_revenue.report_line_id.population_method == 'month' and admin_supp_revenue.net or admin_supp_revenue.balance
    #         admin_supp_gp_bal = admin_supp_gp.report_line_id.population_method == 'month' and admin_supp_gp.net or admin_supp_gp.balance
    #         admin_supp_pct = admin_supp_revenue_bal and admin_supp_gp_bal / admin_supp_revenue_bal or 0
    #
    #         cleaning_svc_revenue_bal = cleaning_svc_revenue.report_line_id.population_method == 'month' and cleaning_svc_revenue.net or cleaning_svc_revenue.balance
    #         cleaning_svc_gp_bal = cleaning_svc_gp.report_line_id.population_method == 'month' and cleaning_svc_gp.net or cleaning_svc_gp.balance
    #         cleaning_svc_pct = cleaning_svc_revenue_bal and cleaning_svc_gp_bal / cleaning_svc_revenue_bal or 0
    #
    #         job_supp_revenue_bal = job_supp_revenue.report_line_id.population_method == 'month' and job_supp_revenue.net or job_supp_revenue.balance
    #         job_supp_gp_bal = job_supp_gp.report_line_id.population_method == 'month' and job_supp_gp.net or job_supp_gp.balance
    #         job_supp_pct = job_supp_revenue_bal and job_supp_gp_bal / job_supp_revenue_bal or 0
    #
    #         ob_revenue_bal = ob_revenue.report_line_id.population_method == 'month' and ob_revenue.net or ob_revenue.balance
    #         ob_gp_bal = ob_gp.report_line_id.population_method == 'month' and ob_gp.net or ob_gp.balance
    #         ob_pct = ob_revenue_bal and ob_gp_bal / ob_revenue_bal or 0
    #
    #         svc_japek_revenue_bal = svc_japek_revenue.report_line_id.population_method == 'month' and svc_japek_revenue.net or svc_japek_revenue.balance
    #         svc_japek_gp_bal = svc_japek_gp.report_line_id.population_method == 'month' and svc_japek_gp.net or svc_japek_gp.balance
    #         svc_japek_pct = svc_japek_revenue_bal and svc_japek_gp_bal / svc_japek_revenue_bal or 0
    #
    #         me_japek_revenue_bal = me_japek_revenue.report_line_id.population_method == 'month' and me_japek_revenue.net or me_japek_revenue.balance
    #         me_japek_gp_bal = me_japek_gp.report_line_id.population_method == 'month' and me_japek_gp.net or me_japek_gp.balance
    #         me_japek_pct = me_japek_revenue_bal and me_japek_gp_bal / me_japek_revenue_bal or 0
    #
    #         total_revenue = civ_cons_revenue_bal + maint_ac_revenue_bal + maint_gd_revenue_bal + maint_stp_revenue_bal\
    #                         + rent_car_revenue_bal + admin_supp_revenue_bal + cleaning_svc_revenue_bal + job_supp_revenue_bal\
    #                         + ob_revenue_bal + svc_japek_revenue_bal + me_japek_revenue_bal
    #         total_gp = civ_cons_gp_bal + maint_ac_gp_bal + maint_gd_gp_bal + maint_stp_gp_bal + rent_car_gp_bal\
    #                    + admin_supp_gp_bal + cleaning_svc_gp_bal + job_supp_gp_bal + ob_gp_bal + svc_japek_gp_bal + me_japek_gp_bal
    #         total_pct = total_revenue and total_gp / total_revenue or 0
    #
    #         ratio = self.env['dashboard.cubes.gp.mbut']
    #         ratio.create({
    #             'company_id': company_id,
    #             'date': date,
    #             'date_mth': date_mth,
    #
    #             'civ_cons_revenue': civ_cons_revenue_bal,
    #             'civ_cons_gp': civ_cons_gp_bal,
    #             'civ_cons_pct': civ_cons_pct,
    #             'civ_cons': '%s:%s' % ('{:,.0f}'.format(civ_cons_gp_bal), '{:,.2%}'.format(civ_cons_pct)),
    #
    #             'maint_ac_revenue': maint_ac_revenue_bal,
    #             'maint_ac_gp': maint_ac_gp_bal,
    #             'maint_ac_pct': maint_ac_pct,
    #             'maint_ac': '%s:%s' % ('{:,.0f}'.format(maint_ac_gp_bal), '{:,.2%}'.format(maint_ac_pct)),
    #
    #             'maint_gd_revenue': maint_gd_revenue_bal,
    #             'maint_gd_gp': maint_gd_gp_bal,
    #             'maint_gd_pct': maint_gd_pct,
    #             'maint_gd': '%s:%s' % ('{:,.0f}'.format(maint_gd_gp_bal), '{:,.2%}'.format(maint_gd_pct)),
    #
    #             'maint_stp_revenue': maint_stp_revenue_bal,
    #             'maint_stp_gp': maint_stp_gp_bal,
    #             'maint_stp_pct': maint_stp_pct,
    #             'maint_stp': '%s:%s' % ('{:,.0f}'.format(maint_stp_gp_bal), '{:,.2%}'.format(maint_stp_pct)),
    #
    #             'rent_car_revenue': rent_car_revenue_bal,
    #             'rent_car_gp': rent_car_gp_bal,
    #             'rent_car_pct': rent_car_pct,
    #             'rent_car': '%s:%s' % ('{:,.0f}'.format(rent_car_gp_bal), '{:,.2%}'.format(rent_car_pct)),
    #
    #             'admin_supp_revenue': admin_supp_revenue_bal,
    #             'admin_supp_gp': admin_supp_gp_bal,
    #             'admin_supp_pct': admin_supp_pct,
    #             'admin_supp': '%s:%s' % ('{:,.0f}'.format(admin_supp_gp_bal), '{:,.2%}'.format(admin_supp_pct)),
    #
    #             'cleaning_svc_revenue': cleaning_svc_revenue_bal,
    #             'cleaning_svc_gp': cleaning_svc_gp_bal,
    #             'cleaning_svc_pct': cleaning_svc_pct,
    #             'cleaning_svc': '%s:%s' % ('{:,.0f}'.format(cleaning_svc_gp_bal), '{:,.2%}'.format(cleaning_svc_pct)),
    #
    #             'job_supp_revenue': job_supp_revenue_bal,
    #             'job_supp_gp': job_supp_gp_bal,
    #             'job_supp_pct': job_supp_pct,
    #             'job_supp': '%s:%s' % ('{:,.0f}'.format(job_supp_gp_bal), '{:,.2%}'.format(job_supp_pct)),
    #
    #             'ob_revenue': ob_revenue_bal,
    #             'ob_gp': ob_gp_bal,
    #             'ob_pct': ob_pct,
    #             'ob': '%s:%s' % ('{:,.0f}'.format(ob_gp_bal), '{:,.2%}'.format(ob_pct)),
    #
    #             'svc_japek_revenue': svc_japek_revenue_bal,
    #             'svc_japek_gp': svc_japek_gp_bal,
    #             'svc_japek_pct': svc_japek_pct,
    #             'svc_japek': '%s:%s' % ('{:,.0f}'.format(svc_japek_gp_bal), '{:,.2%}'.format(svc_japek_pct)),
    #
    #             'me_japek_revenue': me_japek_revenue_bal,
    #             'me_japek_gp': me_japek_gp_bal,
    #             'me_japek_pct': me_japek_pct,
    #             'me_japek': '%s:%s' % ('{:,.0f}'.format(me_japek_gp_bal), '{:,.2%}'.format(me_japek_pct)),
    #
    #             'total_revenue': total_revenue,
    #             'total_gp': total_gp,
    #             'total_pct': total_pct,
    #             'total': '%s:%s' % ('{:,.0f}'.format(total_gp), '{:,.2%}'.format(total_pct)),
    #         })