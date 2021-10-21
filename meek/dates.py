#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manage dates
"""

from copy import copy
import logging
import maya
from tzlocal import get_localzone

days_of_week = ['monday', 'tuesday', 'wednesday',
                'thursday', 'friday', 'saturday', 'sunday']
logger = logging.getLogger(__name__)
tz = str(get_localzone())


def comprehend_date(when):
    """Figure out a datetime for whatever is in the 'when' argument. """
    if isinstance(when, maya.MayaDT):
        return (when, None)
    elif isinstance(when, str):
        pass
    else:
        raise TypeError(
            f'Unexpected type for argument "when": {type(when)} = {repr(when)}')

    today = maya.when('today', tz)
    end_date = None
    if when == '':
        q = 'today'
    else:
        q = when
    if q in ['today', 'yesterday', 'tomorrow']:
        start_date = maya.when(q, tz)
        end_date = copy(start_date)
    elif q in days_of_week:
        today = maya.when('today', tz)
        dow = days_of_week.index(q) + 1
        if dow > today.weekday:
            start_date = maya.when(q, tz, prefer_dates_from='future')
        else:
            start_date = maya.when(q, tz)
        end_date = copy(start_date)
    elif q.startswith('last '):
        q_ultima = q.split()[-1]
        if q_ultima == 'week':
            start_date = maya.when('monday', tz).subtract(weeks=1)
            end_date = start_date.add(days=4)
        elif q_ultima == 'month':
            start_date = today.subtract(months=1).snap('@month')
            end_date = start_date.add(months=1).subtract(days=1)
    elif q.startswith('this '):
        q_ultima = q.split()[-1]
        if q_ultima in ['week', 'month', 'quarter', 'year']:

            if q_ultima == 'week':
                start_date = maya.when('monday', tz)
                kwargs = {'days': 5}
            elif q_ultima == 'quarter':
                start_date = today.snap(f'@month')
                if start_date.month in [2, 5, 8, 11]:
                    start_date = start_date.subtract(months=1)
                elif start_date.month in [3, 6, 9, 12]:
                    start_date = start_date.subtract(months=2)
                kwargs = {'months': 3}
            else:
                start_date = today.snap(f'@{q_ultima}')
                kwargs = {f'{q_ultima}s': 1}
            end_date = start_date.add(**kwargs).subtract(days=1)
        else:
            raise NotImplementedError(q)
    elif q.startswith('next '):
        q_ultima = q.split()[-1]
        today = maya.when('today', tz)
        if q_ultima in days_of_week:
            start_date = today.add(weeks=1)
        elif q_ultima == 'week':
            start_date = maya.when('monday', tz).add(weeks=1)
            end_date = start_date.add(days=4)
        elif q_ultima == 'quarter':
            start_date = today.snap(f'@month')
            if start_date.month in [2, 5, 8, 11]:
                start_date = start_date.subtract(months=1)
            elif start_date.month in [3, 6, 9, 12]:
                start_date = start_date.subtract(months=2)
            start_date = start_date.add(months=3)
            end_date = start_date.add(months=3).subtract(days=1)
        elif q_ultima in ['month', 'year']:
            start_date = today.snap(f'@{q_ultima}')
            if q_ultima == 'quarter':
                if start_date.month in [2, 5, 8, 11]:
                    kwargs = {'months': 2}
                elif start_date.month in [3, 6, 9, 12]:
                    kwargs = {'months': 1}
                    start_date = start_date.subtract(months=2)
                else:
                    kwargs = {'months': 3}
            else:
                kwargs = {f'{q_ultima}s': 1}
            start_date = start_date.add(**kwargs)
            if q_ultima == 'quarter':
                kwargs = {'months': 3}
            end_date = start_date.add(**kwargs).subtract(days=1)
        else:
            raise NotImplementedError(q)
    else:
        start_date = maya.when(q)
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
