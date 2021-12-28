from odoo import models, fields, api, _
from odoo.exceptions import Warning,UserError
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import *

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def populate_cube(self):
        def set_balance(dt, bal):
            month = int(dt.split('-')[1])
            if month == 1:
                balance_01 = bal
            elif month == 2:
                balance_02 = bal
            elif month == 3:
                balance_03 = bal
            elif month == 4:
                balance_04 = bal
            elif month == 5:
                balance_05 = bal
            elif month == 6:
                balance_06 = bal
            elif month == 7:
                balance_07 = bal
            elif month == 8:
                balance_08 = bal
            elif month == 9:
                balance_09 = bal
            elif month == 10:
                balance_10 = bal
            elif month == 11:
                balance_11 = bal
            elif month == 12:
                balance_12 = bal

        query = """
            delete from cube.ratio;
            select aml.account_id, aml.user_type_id, a.group_id, aml.date, 
                   aml.analytic_account_id, aml.company_currency_id, aml.balance,
                   aml.move_id, aml.move_line_id
            from account_move_line aml
                 inner join account_move am on aml.move_id = am.id
                 inner join account_account a on aml.account_id = a.id
            where am.state = 'posted'
        """
        cr = self.env.cr
        # params = (self.env.user.id,)
        cr.execute(query) #, params)
        res = cr.fetchall()

        for r in res:
            account_id = r[0]
            user_type_id = r[1]
            group_id = r[2]
            date = r[3]
            analytic_account_id = r[4]
            currency_id = r[5]
            balance = r[6]
            move_id = r[7]
            move_line_id = r[8]
            balance_01 = balance_02 = balance_03 = balance_04 = balance_05 = balance_06 = 0
            balance_07 = balance_08 = balance_09 = balance_10 = balance_11 = balance_12 = 0
            set_balance(date, balance)
            line = self.env['cube.ratio']
            line.create({
                'account_id': account_id,
                'user_type_id': user_type_id,
                'group_id': group_id,
                'date': date,
                'analytic_account_id': analytic_account_id,
                'currency_id': currency_id,
                'balance': balance,
                'balance_01': balance_01,
                'balance_02': balance_02,
                'balance_03': balance_03,
                'balance_04': balance_04,
                'balance_05': balance_05,
                'balance_06': balance_06,
                'balance_07': balance_07,
                'balance_08': balance_08,
                'balance_09': balance_09,
                'balance_10': balance_10,
                'balance_11': balance_11,
                'balance_12': balance_12,
                'move_id': move_id,
                'move_line_id': move_line_id,
            })
