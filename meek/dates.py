#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manage dates
"""

from copy import copy
import logging
import maya
from tzlocal import get_localzone


logger = logging.getLogger(__name__)


def iso_datestamp(dt: maya.MayaDT):
    if isinstance(dt, maya.MayaDT):
        return dt.iso8601().split('T')[0]
    else:
        raise TypeError(f'Unexpected value for dt: {type(dt)}={repr(dt)}')


def comprehend_date(when):
    if isinstance(when, maya.MayaDT):
        return (when, None)
    elif isinstance(when, str):
        pass
    else:
        raise TypeError(
            f'Unexpected type for argument "when": {type(when)} = {repr(when)}')

    end_date = None
    tz = str(get_localzone())
    if when == '':
        q = 'today'
    else:
        q = when
    days_of_week = ['monday', 'tuesday', 'wednesday',
                    'thursday', 'friday', 'saturday', 'sunday']
    if q in ['today', 'yesterday', 'tomorrow']:
        start_date = maya.when(q, tz)
        end_date = copy(start_date)
    elif q in days_of_week:
        today = maya.when('today', tz)
        dow = days_of_week.index(q) + 1
        print(f'today.weekday: {today.weekday}')
        print(f'dow: {dow}')
        if dow > today.weekday:
            print('foo')
            start_date = maya.when(q, tz, prefer_dates_from='future')
        else:
            print('bar')
            start_date = maya.when(q, tz)
        end_date = copy(start_date)
    elif q.startswith('this '):
        q_ultima = q.split()[-1]
        if q_ultima in ['week', 'month', 'quarter', 'year']:
            today = maya.when('today', tz)
            if q_ultima == 'quarter':
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
        if q_ultima in ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']:
            start_date = maya.when(
                q_ultima, tz, prefer_dates_from='future')
        elif q_ultima in ['week', 'month', 'quarter', 'year']:
            today = maya.when('today', tz)
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
