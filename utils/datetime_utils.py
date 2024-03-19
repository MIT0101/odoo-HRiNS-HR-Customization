import datetime

import pytz
from dateutil import relativedelta


def format_date(date):
    return date.strftime("%Y-%m-%d") if date else None


def format_date_time(date_time, user_tz=pytz.utc):
    date_time_res = get_date_time_from_user_tz(date_time, user_tz)
    if not date_time_res:
        return None
    return date_time_res.strftime("%Y-%m-%d %H:%M:%S")


def get_date_time_from_user_tz(date_time, user_tz=pytz.utc):
    if not date_time:
        return None
    date_time.astimezone(pytz.utc)
    return date_time.astimezone(user_tz)


def generate_date_range(start_date, end_date):
    date_range = []
    while start_date <= end_date:
        date_range.append(start_date)
        start_date += datetime.timedelta(days=1)
    return date_range
