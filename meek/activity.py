#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3 package template (changeme)
"""

from meek.norm import norm
import logging
import maya
from tzlocal import get_localzone
from uuid import uuid4, UUID

logger = logging.getLogger(__name__)
tz = str(get_localzone())


class Activity:

    def __init__(self, **kwargs):
        self._id = None
        self._tags = set()
        self._title = None
        self._due = None
        self._complete = False
        for k, arg in kwargs.items():
            # print(f'{k}: "{arg}"')
            setattr(self, k, arg)
        if self._id is None:
            self._id = uuid4()

    def asdict(self):
        d = {
            'id': self.id.hex,
            'title': self.title,
            'complete': self.complete
        }
        for attrname in ['due', 'tags', 'complete']:
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
            else:
                raise TypeError(f'activity.{attrname}: {type(v)} = {repr(v)}')
            d[attrname] = val
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

    @ property
    def due(self):
        return self._due

    @ due.setter
    def due(self, value):
        if isinstance(value, str):
            dt = maya.when(value, tz)
        else:
            raise TypeError(
                f'value: {type(value)} = {repr(value)}, expected {str}')
        dt_s = dt.iso8601().split('T')[0]
        today = maya.when('today', tz)
        today = today.snap_tz('@d+6h', tz)
        today_s = today.iso8601().split('T')[0]
        if dt_s < today_s:
            logger.warning(
                f'Supplied due date ({dt_s}) is earlier than today ({today_s})')
        self._due = dt_s

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

    @ property
    def title(self):
        return self._title

    @ title.setter
    def title(self, value):
        if not isinstance(value, str):
            raise TypeError(f'{type(value)}: {repr(value)}')
        self._title = norm(value)

    @property
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

    def __str__(self):
        return f'{self.title}'

    def __repr__(self):
        return f'Activity(title="{self.title}")'
