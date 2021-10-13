#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3 package template (changeme)
"""

from meek.norm import norm
import logging
from uuid import uuid4, UUID

logger = logging.getLogger(__name__)


class Activity:

    def __init__(self, **kwargs):
        self._id = None
        self._tags = set()
        self._title = None
        for k, arg in kwargs.items():
            # print(f'{k}: "{arg}"')
            setattr(self, k, arg)
        if self._id is None:
            self._id = uuid4()

    def asdict(self):
        d = {
            'id': self.id.hex,
            'title': self.title,
            'tags': self.tags
        }
        return d

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
