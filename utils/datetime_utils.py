import datetime

import pytz
from dateutil import relativedelta


def format_date(date):
    return date.strftime("%Y-%m-%d") if date else None


def format_date_time(date_time, user_tz=pytz.utc):
    if not date_time:
        return None
    date_time.astimezone(pytz.utc)
    date_in_user_tz = date_time.astimezone(user_tz)
    return date_in_user_tz.strftime("%Y-%m-%d %H:%M:%S")


def generate_date_range(start_date, end_date):
    date_range = []
    while start_date <= end_date:
        date_range.append(start_date)
        start_date += datetime.timedelta(days=1)
    return date_range
