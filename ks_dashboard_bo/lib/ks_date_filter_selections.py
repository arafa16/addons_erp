# -*- coding: utf-8 -*-

from odoo.fields import datetime
from datetime import timedelta
from odoo.addons.resource.models.resource import to_naive_utc


def ks_get_date(ks_date_filter_selection, self):

    timezone = self._context.get('tz') or self.env.user.partner_id.tz or 'UTC'
    self_tz = self.with_context(tz=timezone)

    series = ks_date_filter_selection
    return eval("ks_date_series_" + series.split("_")[0])(series.split("_")[1], self_tz)


# Last Specific Days Ranges : 7, 30, 90, 365
def ks_date_series_l(ks_date_selection, self_tz):
    ks_date_data = {}
    date_filter_options = {
        'day': 0,
        'week': 7,
        'month': 30,
        'quarter': 90,
        'year': 365,
        'past': False,
        'future': False,
        'fiscal': False,
    }

    if ks_date_selection == 'fiscal':
        return ks_get_date_range_from_last_fiscal_year(self_tz)

    end_date = datetime.strptime(datetime.now().strftime("%Y-%m-%d 23:59:59"),
                                                          '%Y-%m-%d %H:%M:%S')

    start_date = datetime.strptime((datetime.now() - timedelta(
        days=date_filter_options[ks_date_selection])).strftime("%Y-%m-%d 00:00:00"), '%Y-%m-%d %H:%M:%S')

    ks_date_data["selected_end_date"] = to_naive_utc(end_date, self_tz)
    ks_date_data["selected_start_date"] = to_naive_utc(start_date, self_tz)
    return ks_date_data


# Current Date Ranges : Week, Month, Quarter, year
def ks_date_series_t(ks_date_selection, self_tz):
    return eval("ks_get_date_range_from_" + ks_date_selection)("current", self_tz)


# Previous Date Ranges : Week, Month, Quarter, year
def ks_date_series_ls(ks_date_selection, self_tz):
    return eval("ks_get_date_range_from_" + ks_date_selection)("previous", self_tz)


# Next Date Ranges : Day, Week, Month, Quarter, year
def ks_date_series_n(ks_date_selection, self_tz):
    return eval("ks_get_date_range_from_" + ks_date_selection)("next", self_tz)


def ks_get_date_range_from_day(date_state, self_tz):
    ks_date_data = {}

    date = datetime.now()

    if date_state == "previous":
        date = date - timedelta(days=1)
    elif date_state == "next":
        date = date + timedelta(days=1)
    start_date = datetime(date.year, date.month, date.day)
    end_date = datetime(date.year, date.month, date.day) + timedelta(days=1, seconds=-1)
    ks_date_data["selected_start_date"] = to_naive_utc(start_date, self_tz)
    ks_date_data["selected_end_date"] = to_naive_utc(end_date, self_tz)
    return ks_date_data


def ks_get_date_range_from_week(date_state, self_tz):
    ks_date_data = {}

    date = datetime.now()

    if date_state == "previous":
        date = date - timedelta(days=7)
    elif date_state == "next":
        date = date + timedelta(days=7)

    date_iso = date.isocalendar()
    year = date_iso[0]
    week_no = date_iso[1]
    start_date = datetime.strptime('%s-W%s-1' % (year, week_no - 1), "%Y-W%W-%w")
    end_date = start_date + timedelta(days=6, hours=23, minutes=59,
                                                               seconds=59, milliseconds=59)
    ks_date_data["selected_start_date"] = to_naive_utc(start_date, self_tz)
    ks_date_data["selected_end_date"] = to_naive_utc(end_date, self_tz)
    return ks_date_data


def ks_get_date_range_from_month(date_state, self_tz):
    ks_date_data = {}

    date = datetime.now()
    year = date.year
    month = date.month

    if date_state == "previous":
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    elif date_state == "next":
        month += 1
        if month == 13:
            month = 1
            year += 1

    end_year = year
    end_month = month
    if month == 12:
        end_year += 1
        end_month = 1
    else:
        end_month += 1
    start_date = datetime(year, month, 1)
    end_date = datetime(end_year, end_month, 1) - timedelta(seconds=1)
    ks_date_data["selected_start_date"] = to_naive_utc(start_date, self_tz)
    ks_date_data["selected_end_date"] = to_naive_utc(end_date, self_tz)
    return ks_date_data


def ks_get_date_range_from_quarter(date_state, self_tz):
    ks_date_data = {}

    date = datetime.now()
    year = date.year
    quarter = int((date.month - 1) / 3) + 1

    if date_state == "previous":
        quarter -= 1
        if quarter == 0:
            quarter = 4
            year -= 1
    elif date_state == "next":
        quarter += 1
        if quarter == 5:
            quarter = 1
            year += 1

    start_date = datetime(year, 3 * quarter - 2, 1)
    ks_date_data["selected_start_date"] = to_naive_utc(start_date, self_tz)

    month = 3 * quarter
    remaining = int(month / 12)
    end_date = datetime(year + remaining, month % 12 + 1, 1) - timedelta(seconds=1)
    ks_date_data["selected_end_date"] = to_naive_utc(end_date, self_tz)

    return ks_date_data


def ks_get_date_range_from_year(date_state, self_tz):
    ks_date_data = {}

    date = datetime.now()
    year = date.year

    if date_state == "previous":
        year -= 1
    elif date_state == "next":
        year += 1
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    ks_date_data["selected_start_date"] = to_naive_utc(start_date, self_tz)
    ks_date_data["selected_end_date"] = to_naive_utc(end_date, self_tz)
    return ks_date_data


def ks_get_date_range_from_past(date_state, self_tz):
    ks_date_data = {}
    date = datetime.now()
    ks_date_data["selected_start_date"] = False
    ks_date_data["selected_end_date"] = date
    return ks_date_data


def ks_get_date_range_from_pastwithout(date_state, self_tz):
    ks_date_data = {}
    date = datetime.now()
    hour = date.hour + 1
    date = date - timedelta(hours=hour)
    ks_date_data["selected_start_date"] = False
    ks_date_data["selected_end_date"] = date
    return ks_date_data


def ks_get_date_range_from_future(date_state, self_tz):
    ks_date_data = {}
    date = datetime.now()
    ks_date_data["selected_start_date"] = date
    ks_date_data["selected_end_date"] = False
    return ks_date_data


def ks_get_date_range_from_futurestarting(date_state, self_tz):
    ks_date_data = {}
    date = datetime.now()
    hour = (24 - date.hour) + 1
    date = date + timedelta(hours=hour)
    start_date = datetime(date.year, date.month, date.day)
    ks_date_data["selected_start_date"] = to_naive_utc(start_date, self_tz)
    ks_date_data["selected_end_date"] = False
    return ks_date_data

def ks_get_date_range_from_fiscal(date_state, self_tz):
    ks_date_data = {}

    date = datetime.now()
    year = date.year
    if date.month == 1 or date.month == 2 or date.month == 3:
        year = year - 1
    start_date = datetime(year, 4, 1)
    end_date = datetime(year + 1, 4, 1) - timedelta(seconds=1)
    ks_date_data["selected_start_date"] = to_naive_utc(start_date, self_tz)
    ks_date_data["selected_end_date"] = to_naive_utc(end_date, self_tz)
    return ks_date_data

def ks_get_date_range_from_last_fiscal_year(self_tz):
    ks_date_data = {}
    date = datetime.now()
    year = date.year
    if date.month == 1 or date.month == 2 or date.month == 3:
        year = year - 1
    start_date = datetime(year-1, 4, 1)
    end_date = datetime(year, 4, 1) - timedelta(seconds=1)

    ks_date_data["selected_start_date"] = to_naive_utc(start_date, self_tz)
    ks_date_data["selected_end_date"] = to_naive_utc(end_date, self_tz)
    return ks_date_data