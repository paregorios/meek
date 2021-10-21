#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manage dates
"""

from copy import copy
import logging
import math
import maya
import re
from tzlocal import get_localzone

days_of_week = ['monday', 'tuesday', 'wednesday',
                'thursday', 'friday', 'saturday', 'sunday']
logger = logging.getLogger(__name__)
rx_descriptive_date = re.compile(
    r'^(?P<relation>last|next|this)? ?(?P<period>monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|month|quarter|year)$')
tz = str(get_localzone())


def quarter(when):
    if isinstance(when, int):
        m = when
    elif isinstance(when, maya.MayaDT):
        m = when.month
    else:
        raise TypeError(
            f'Unexpected type for argument "when": {type(when)} = {repr(when)}')
    if m < 1 or m > 12:
        raise ValueError(
            f'Month number ({m}) derived from argument "when" out of range. Expected 1-12.'
        )
    q = math.ceil(m/3)
    start_m = (q - 1) * 3 + 1
    end_m = start_m + 2
    return {
        'quarter': q,
        'start_month': start_m,
        'end_month': end_m
    }


def comprehend_date(when):
    """Figure out a datetime for whatever is in the 'when' argument. """
    if isinstance(when, maya.MayaDT):
        return (when, None)
    elif isinstance(when, str):
        pass
    else:
        raise TypeError(
            f'Unexpected type for argument "when": {type(when)} = {repr(when)}')
    if when == '':
        when = 'today'
    m = rx_descriptive_date.match(when)
    if m is None:
        start_date = maya.when(when, tz)
        end_date = copy(start_date)
    else:
        relation = m.group('relation')
        period = m.group('period')
        today = maya.when('today', tz)
        if period == 'quarter':
            q = quarter(today)
            start_date = maya.when(f'{today.year}-{q["start_month"]}-1', tz)
            end_date = maya.when(
                f'{today.year}-{q["end_month"]}-1', tz).add(months=1).subtract(days=1)
            delta = {'months': 3}
        elif period == 'week':
            # for meek, "week" means "work week", i.e., monday-friday
            start_date = today.snap('@week').add(days=1)
            end_date = start_date.add(days=4)
            delta = {'weeks': 1}
        elif period in days_of_week:
            start_date = maya.when(period, tz)
            if start_date.weekday > today.weekday:
                start_date = start_date.add(weeks=1)
            end_date = copy(start_date)
            delta = {'weeks': 1}
        else:
            start_date = today.snap(f'@{period}')
            kwargs = {f'{period}s': 1}
            end_date = start_date.add(**kwargs).subtract(days=1)
            delta = {f'{period}s': 1}
        if relation is not None:
            if relation == 'last':
                start_date = start_date.subtract(**delta)
                end_date = end_date.subtract(**delta)
            elif relation == 'this':
                pass
            elif relation == 'next':
                start_date = start_date.add(**delta)
                end_date = end_date.add(**delta)
    return (start_date, end_date)


def dow_future_proof(when, dt: maya.MayaDT):
    """ If 'when' is a day of the week, make sure dt is in the future, not past. """
    if isinstance(when, str):
        if when in days_of_week:
            today = maya.when('today', tz)
            if today.weekday >= dt.weekday:
                dt = dt.add(days=7)
    return dt


def iso_datestamp(dt: maya.MayaDT):
    """Return just the date part of the ISO 8601 string for the MayaDT """
    if isinstance(dt, maya.MayaDT):
        return dt.iso8601().split('T')[0]
    else:
        raise TypeError(f'Unexpected value for dt: {type(dt)}={repr(dt)}')
