#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3 package template (changeme)
"""

from collections import deque
from meek.norm import norm
import logging
import maya
from tzlocal import get_localzone
from uuid import uuid4, UUID

logger = logging.getLogger(__name__)
tz = str(get_localzone())


class Event:

    def __init__(self, what: str, when=None):
        if when is None:
            self.when = maya.now()
        else:
            self.when = maya.when(when)
        self.what = what

    def asdict(self):
        d = {
            'what': self.what,
            'when': self.when.iso8601()
        }
        return d


class Activity:

    def __init__(self, mode='live', **kwargs):
        self._id = None
        self._tags = set()
        self._title = None
        self._due = None
        self._complete = False
        self._history = deque()
        self.supported_intervals = [
            'none', 'day', 'workday', 'week', 'month', 'quarter', 'year']
        self._interval = None
        self.mode = mode
        # keeps events out of history if mode is not "live", e.g., reload from json
        for k, arg in kwargs.items():
            if k == 'history':
                for d in arg:
                    self._history.append(Event(**d))
                continue
            try:
                setattr(self, k, arg)
            except AttributeError as err:
                msg = str(
                    err) + f' "{k}". Desired value: {repr(arg)} of type {type(arg)}.'
                raise AttributeError(msg)
        self.mode = 'live'
        if self._id is None:
            self._id = uuid4()

    def asdict(self):
        d = {
            'id': self.id.hex,
            'title': self.title,
            'complete': self.complete
        }
        for attrname in ['due', 'tags', 'interval']:
            v = getattr(self, attrname)
            if v is None:
                continue
            elif isinstance(v, (str, list)):
                if len(v) == 0:
                    continue
                val = v
            elif isinstance(v, set):
                if len(v) == 0:
                    continue
                val = list(v)
            elif isinstance(v, maya.MayaDT):
                val = v.iso8601()
            elif isinstance(v, bool):
                val = v
            else:
                raise TypeError(f'activity.{attrname}: {type(v)} = {repr(v)}')
            d[attrname] = val
        if len(self._history) != 0:
            d['history'] = [e.asdict() for e in self.history]
        return d

    @ property
    def complete(self):
        return self._complete

    @ complete.setter
    def complete(self, value):
        if isinstance(value, bool):
            v = value
        elif isinstance(value, int):
            v = bool(value)
        else:
            raise TypeError(
                f'Value ({repr(value)} is {type(value)}. Expected {bool}.')
        self._complete = v
        if self.mode == 'live':
            self._append_event(f'complete={self.complete}')
        self._due_interval()

    @ property
    def due(self):
        return self._due

    @ due.setter
    def due(self, value):
        if isinstance(value, str):
            dt = maya.when(value, tz)
        elif isinstance(value, maya.MayaDT):
            dt = value
        else:
            raise TypeError(
                f'value: {type(value)} = {repr(value)}, expected {str} or {maya.MayaDT}')
        dt_s = dt.iso8601().split('T')[0]
        today = maya.when('today', tz)
        today = today.snap_tz('@d+6h', tz)
        today_s = today.iso8601().split('T')[0]
        if dt_s < today_s:
            logger.warning(
                f'Supplied due date ({dt_s}) is earlier than today ({today_s})')
        self._due = dt_s
        if self.mode == 'live':
            self._append_event(f'due={self.due}')

    @ property
    def history(self):
        return list(self._history)

    @ property
    def id(self):
        return self._id

    @ id.setter
    def id(self, value):
        if isinstance(value, UUID):
            self._id = value
        elif isinstance(value, str):
            self._id = UUID(value)
        else:
            raise TypeError(f'{type(value)}: {repr(value)}')
        if self.mode == 'live':
            self._append_event(f'id={self.id}')

    # interval: how soon to make due after completion
    @ property
    def interval(self):
        return self._interval

    @ interval.setter
    def interval(self, value):
        if not isinstance(value, str):
            raise TypeError(f'value: {type(value)}: {repr(value)}')
        if value not in self.supported_intervals:
            support_string = ', '.join(
                [f'"{s}"' for s in self.supported_intervals])
            raise ValueError(
                f'Unexpected interval value "{value}". Supported values are: {support_string}.')
        if value == 'none':
            self._interval = None
        else:
            self._interval = value
        if self.mode == 'live':
            self._append_event(f'interval={self.interval}')

    @ property
    def tags(self):
        return list(self._tags)

    @ tags.setter
    def tags(self, value):
        if isinstance(value, str):
            v = [value, ]
        elif isinstance(value, list):
            v = value
        else:
            raise TypeError(f'value: {type(value)}={repr(value)}')
        self._tags.update(v)
        if self.mode == 'live':
            self._append_event(f'tags={self.tags}')

    @ property
    def title(self):
        return self._title

    @ title.setter
    def title(self, value):
        if not isinstance(value, str):
            raise TypeError(f'{type(value)}: {repr(value)}')
        self._title = norm(value)
        if self.mode == 'live':
            self._append_event(f'title={self.title}')

    @ property
    def words(self):
        attrs = [a for a in dir(self) if a != '_id' and a.startswith(
            '_') and not a.startswith('__')]
        attrvals = set()
        for a in attrs:
            v = getattr(self, a)
            if isinstance(v, str):
                attrvals.update(v.split())
            elif isinstance(v, (list, set)):
                for vv in v:
                    attrvals.update(vv.split())
        return attrvals

    def _append_event(self, what: str):
        e = Event(what)
        self._history.append(e)

    def _due_interval(self):
        """Reset due date if an interval is set."""
        if self.interval is None:
            return
        if self.interval == 'quarter':
            kwargs = {'months': 3}
        else:
            kwargs = {f'{self.interval}s': 1}
        today = maya.when('today', tz)
        when = today.add(**kwargs)
        self.due = when
        self.complete = False

    def __str__(self):
        return f'{self.title}'

    def __repr__(self):
        return f'Activity(title="{self.title}")'
