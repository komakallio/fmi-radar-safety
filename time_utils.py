# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from math import floor


def floor_to_int(x, base=5):
    """Rounds to nearest lower base integer. Eg. 0..4 round to 0, 5..9 round
    to 5 etc. when base == 5."""
    return int(base * floor(float(x)/base))


def floor_time(date_object):
    """Floors a datetime object to the nearest lower 5 minutes."""
    floored_time = date_object.replace(minute=floor_to_int(date_object.minute), second=0, microsecond=0)
    return floored_time


def current_radar_time(offset=None):
    """Returns the current time floored to the nearest lower five minutes.
    The offset can be used to set the time
    back in case radar images aren't immediately available."""
    current_time = floor_time(datetime.utcnow())
    if offset:
        offset_delta = timedelta(minutes=offset)
        current_time = current_time + offset_delta
    return current_time


def datetime_to_wms_string(datetime_object):
    return datetime_object.isoformat() + 'Z'
