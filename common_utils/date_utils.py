import datetime as dtt
import time
from datetime import datetime, timedelta

import iso8601
import numpy as np
import pandas as pd
import pytz
from dateutil import parser
from pandas.tseries.frequencies import to_offset

ACCEPTED_FREQUENCIES = ["S", "T", "H", "D"]


def check_datetime(dt: datetime) -> datetime:
    """Input validation on a datetime. Timezone is assumed to be UTC.

    Parameters
    ----------
    dt : datetime

    Returns
    -------
    dt_converted : converted and validated datetime (with a tzinfo).
    """
    if dt != dt:  # pandas NaT weirdly verify isinstance(dt, datetime)
        raise ValueError("NaT datetime are not supported")

    if not isinstance(dt, datetime):  # (is also ok if type is pandas Timestamp)
        raise ValueError("Expected a datetime instance, got {} instead".format(type(dt)))

    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()

    if not dt.tzinfo:
        dt = pytz.UTC.localize(dt)

    elif dt.tzinfo != pytz.UTC and dt.tzinfo != dtt.timezone.utc:
        raise ValueError("Expected a UTC timezone, got {}".format(dt.tzinfo))
    if dt < datetime(1970, 1, 1).replace(tzinfo=pytz.UTC):
        raise ValueError("Datetime must be larger than 0 unix epoch time")

    return dt


def check_datetimes(start_dt, end_dt):
    """Input validation on a start and end datetime.

    Parameters
    ----------
    start_dt : datetime

    end_dt : datetime assumed to be later than start_dt

    Returns
    -------
    start_dt, end_dt : converted and validated datetimes (with a tzinfo).
    """

    start_dt = check_datetime(start_dt)
    end_dt = check_datetime(end_dt)

    if not start_dt <= end_dt:
        raise ValueError("start_date is after end_date")

    return start_dt, end_dt


def unixepoch2datetime(unixepoch, milliseconds=False):
    """Given a timestamp, it returns a datetime object.

    Parameters
    ----------
    unixepoch : int
       Timestamp. It can have either a second or millisecond precision
    milliseconds : bool
       True if the timestamp has a millisecond precision, False otherwise

    Returns
    -------
    time : datetime
       Datetime object corresponding to the original timestamp
    """
    if milliseconds:
        unixepoch = float(unixepoch) / 1000.0

    time = pytz.UTC.localize(datetime.utcfromtimestamp(unixepoch))

    return time


def datetime2unixepoch(dt, milliseconds=False):
    """Utility to transform a datetime instance into an unix epoch represented as an int.

    Parameters
    ----------
    dt: datetime

    Returns
    -------
    int
        unix epoch
    """
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    else:
        dt = dt.astimezone(pytz.UTC)

    epoch = pytz.UTC.localize(datetime.utcfromtimestamp(0))
    delta = dt - epoch

    result = delta.total_seconds()
    if milliseconds:
        result *= 1000

    return int(result)


def unixepoch_now(milliseconds=False):
    t = time.time()
    if milliseconds:
        t *= 10**3
    return round(t)


def valid_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


def valid_date_tz(s):
    try:
        return parse_date_if_necessary(datetime.strptime(s, "%Y-%m-%d"), to_utc=True)
    except ValueError as e:
        return iso8601.parse_date(s)


def valid_datetime(s):
    """Parse a string to a valid datetime.

    Parameters
    ----------
    s : str
        The string representation of datetime.

    Return
    ------
    datetime
        Datetime parsed from the string.
    """

    return iso8601.parse_date(s)


def parse_date_if_necessary(dt, to_utc=False, no_tz=False):
    """Parse datetime from string or null and modify timezone if necessary.

    Parameters
    ----------
    dt : datetime or str or null
        Valid representation of datetime, can be either time-zone aware or not.
    to_utc : bool
        Whether to convert to utc timezone.
    no_tz : bool
        Whether to remove timezone.

    Return
    ------
    datetime
        Datetime with expected timezone info.
    """

    if pd.isnull(dt):
        dt = pd.to_datetime(np.nan)
    elif isinstance(dt, str):
        dt = parser.parse(dt)
    elif not isinstance(dt, datetime):
        raise ValueError("Expected a datetime instance, got {} instead".format(type(dt)))

    if dt.replace(tzinfo=pytz.UTC) < datetime(1970, 1, 1).replace(tzinfo=pytz.UTC):
        raise ValueError("Datetime must be larger than 1970-01-01")

    if to_utc:
        dt = convert_to_utc(dt)
    if no_tz:
        dt = dt.replace(tzinfo=None)

    return dt


def convert_to_utc(d):
    """Convert datetime to utc.

    Parameters
    ----------
    d : datetime
        It can be both time-zone aware and not

    Return
    ------
    d : datetime
        Datetime with UTC timezone
    """
    if d.tzinfo is None:
        d = d.replace(tzinfo=pytz.UTC)
    else:
        d = d.astimezone(tz=pytz.UTC)

    return d


def str_to_timedelta(frequency):
    """Return DateOffset object from string or tuple representation or datetime.timedelta object

    Parameters
    ----------

    frequency : string or tuple representation or datetime.timedelta object

    Returns
    -------
    datetime.timedelta
    """

    if not isinstance(frequency, str):
        raise TypeError("Expected a string, got a {}".format(type(frequency)))

    if frequency[-1] not in ACCEPTED_FREQUENCIES:
        raise ValueError("Unsupported frequency {}".format(frequency[-1]))

    return pd.Timedelta(to_offset(frequency)).to_pytimedelta()


def split_date_interval(start, end, max_interval):
    """Split a date interval [start, end] into smaller intervals of maximum length max_interval

    Parameters
    ----------
    start: datetime
    end: datetime
    max_interval: timedelta

    Returns
    -------
    intervals: list of tuple(start: datetime, end: datetime)

    Examples
    --------
    one interval |---------| with max_interval -- returns 5 intervals |--|--|--|--|-|
    """
    if max_interval <= timedelta(0):
        raise ValueError(f"max_interval should be positive. (given {max_interval})")

    if start >= end:
        raise ValueError(
            f"the start date should be strictly before end date. Given interval ({start} - {end})"
        )

    intervals = []
    tmp_start = start
    tmp_end = min(start + max_interval, end)
    while tmp_start < end:
        intervals.append((tmp_start, tmp_end))
        tmp_start += max_interval
        tmp_end = min(tmp_start + max_interval, end)
    return intervals


def hour_range(start_dt, end_dt):
    """Yield successive hour from start_date to end_date

    Parameters
    ----------
    start_dt : datetime.datetime
        will be truncated to hour precision. Included in returns.
    end_dt :  datetime.datetime
        will be truncated to hour precision. Included in returns.
    """

    start_dt, end_dt = check_datetimes(start_dt, end_dt)

    start_dt = start_dt.replace(minute=0, second=0, microsecond=0)
    end_dt = end_dt.replace(minute=0, second=0, microsecond=0)
    hours = int((end_dt - start_dt).total_seconds() / 3600.0)

    for n in range(hours + 1):
        yield start_dt + timedelta(hours=n)


def daterange(start_dt, end_dt):
    """Yield successive dates from start_date to end_date

    :param start_dt: datetime.datetime
    :param end_dt:  datetime.datetime
    """

    start_dt, end_dt = check_datetimes(start_dt, end_dt)

    # TODO: perhaps add function for checking time? Would it be reused?
    assert start_dt.time() == datetime.min.time(), "start_dt should not contain time, {}".format(
        start_dt.time()
    )
    assert end_dt.time() == datetime.min.time(), "end_dt should not contain time, {}".format(
        end_dt.time()
    )

    for n in range((end_dt - start_dt).days + 1):
        yield start_dt + timedelta(n)


def daterange_intervals(start_dt, end_dt):
    """List of daily date intervals

    Parameters
    ----------
    start_dt : datetime
        first date we consider

    end_dt : datetime
        last date we consider - it is inclusive

    Returns
    -------
    list of tuples:
        each tuple represents the full span of that day i.e.
        date:00:00.000000 to date:23:59.999999

    """
    intervals = []
    for dt in daterange(start_dt, end_dt):
        intervals.append((dt, dt + timedelta(days=1, microseconds=-1)))

    return intervals


def datetime2seconds(dt):
    """Utility to transform datetime instance into unix epoch time measured in seconds"""
    dt = check_datetime(dt)

    epoch = check_datetime(datetime.utcfromtimestamp(0))
    delta = dt - epoch

    result = int(delta.total_seconds())

    return result


def seconds2datetime(seconds):
    """Utility to transform unix epoch seconds to datetime.datetime"""
    return check_datetime(datetime.utcfromtimestamp(seconds))


def datetime2nanos(dt):
    """Utility to transform datetime instance into unix epoch time measured in nanseconds

    :param dt:
    :return:
    """
    dt = check_datetime(dt)

    epoch = check_datetime(datetime.utcfromtimestamp(0))
    delta = dt - epoch

    result = int(delta.total_seconds() * (10**6)) * (10**3)  # better idea?

    return result


def nanos2datetime(nanoseconds):
    """Utility to transform unix epoch nanoseconds to datetime.datetime

    :param nanoseconds: int, unix epoch time in nanoseconds
    :return:
    """

    return seconds2datetime(nanoseconds / 10**9)