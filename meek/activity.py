#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3 package template (changeme)
"""

from collections import deque
from meek.dates import comprehend_date, dow_future_proof, iso_datestamp
from meek.norm import norm
import logging
import maya
from tzlocal import get_localzone
from uuid import uuid4, UUID

logger = logging.getLogger(__name__)
tz = str(get_localzone())


class Event:
    """An entry in the Activity history."""

    def __init__(self, what: str, when=None):
        if when is None:
            self.when = maya.when('today', tz)
        else:
            self.when = maya.when(when, tz)
        self.what = what

    def asdict(self):
        d = {
            'what': self.what,
            'when': self.when.iso8601()
        }
        return d


class Activity:
    """Something you want or need to do."""

    def __init__(self, mode='live', **kwargs):
        self._id = None
        self._tags = set()
        self._title = None
        self._due = None
        self._not_before = None
        self._complete = False
        self._project = False
        self._tasks = set()
        self._history = deque()
        self.supported_intervals = [
            'none', 'day', 'workday', 'week', 'biweekly', 'month', 'quarter', 'year']
        self._interval = None
        self.mode = mode
        # keeps events out of history if mode is not "live", e.g., reload from json
        self._notes = dict()
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
        for attrname in ['due', 'tags', 'interval', 'not_before', 'project', 'tasks', 'notes']:
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
        if value is None:
            v = False
        elif isinstance(value, bool):
            v = value
        elif isinstance(value, int):
            v = bool(value)
        elif isinstance(value, str) and value.lower() in ['false', 'true']:
            if value.lower() == 'false':
                v = False
            else:
                v = True
        else:
            raise TypeError(
                f'Value ({repr(value)} is {type(value)}. Expected {bool}.')
        self._complete = v
        if self.mode == 'live':
            self._append_event(f'complete={self.complete}')
        if self._complete:
            self._due_interval()

    @ property
    def due(self):
        return self._due

    @ due.setter
    def due(self, value):
        start_dt, end_dt = comprehend_date(value)
        if end_dt is not None:
            dt = end_dt
        else:
            dt = start_dt
        dt = dow_future_proof(value, dt)
        self._due = iso_datestamp(dt)
        if self.mode == 'live':
            self._append_event(f'due={self.due}')

    @ property
    def history(self):
        return list(self._history)

    def reset_history(self):
        self._history = deque([e for e in self._history if e.what in [
                              'title', 'tags', 'id', 'interval']])

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

    # notes

    @ property
    def notes(self):
        note_list = [(n, k) for k, n in self._notes.items()]
        note_list.sort(key=lambda t: t[1])
        return note_list

    @ notes.setter
    def notes(self, value):
        for v, k in value:
            self._notes[k] = v

    @ notes.deleter
    def notes(self):
        self._notes = dict()

    def add_note(self, value):
        k = maya.now().iso8601()
        self._notes[k] = norm(value)

    # not before: keep out of most listings until this date

    @ property
    def not_before(self):
        return self._not_before

    @ not_before.setter
    def not_before(self, value):
        if value is None or value in ['none', '']:
            self._not_before = None
        else:
            start_dt, end_dt = comprehend_date(value)
            tomorrow = maya.when('tomorrow', tz)
            if start_dt >= tomorrow:
                self._not_before = iso_datestamp(start_dt)
            else:
                self._not_before = start_dt
            if self.mode == 'live':
                self._append_event(f'not_before={self.due}')

    @ not_before.deleter
    def not_before(self):
        self._not_before = None

    # project: this activity is a project (True) or not
    # projects have subordinate tasks, which are other activities
    @property
    def project(self):
        return self._project

    @ project.setter
    def project(self, value):
        if isinstance(value, bool):
            val = value
        elif isinstance(value, str):
            v = value.lower()
            if v == 'true':
                val = True
            elif v == 'false':
                val = False
            else:
                ValueError(
                    f'Expected string value like "false" or "true" but got "{value}".'
                )
        else:
            raise TypeError(
                f'Expected value of type {bool} but got {type(value)} = {repr(value)}')
        if not val:
            if len(self._tasks) > 0:
                raise RuntimeError(
                    f'Attempt to set project to false but there are still tasks.')
        self._project = val

    @ property
    def tags(self):
        return list(self._tags)

    @ tags.setter
    def tags(self, value):
        logger.debug(f'>>> {value} <<<')
        if value is None:
            self._tags = set()
        else:
            if isinstance(value, str):
                values = [value, ]
            elif isinstance(value, list):
                values = value
            else:
                raise TypeError(f'value: {type(value)}={repr(value)}')
            logger.debug(f'self._tags: {repr(self._tags)}')
            remove = set([v[1:] for v in values if v.startswith('-')])
            logger.debug(f'remove: {repr(remove)}')
            add = set([v for v in values if not v.startswith('-')])
            logger.debug(f'add: {repr(add)}')
            self._tags.update(add)
            self._tags.difference_update(remove)
            logger.debug(f'self._tags: {repr(self._tags)}')
        if self.mode == 'live':
            self._append_event(f'tags={self.tags}')

    # tasks: activities subordinate to this activity, which is therefore a project

    @ property
    def tasks(self):
        return self._tasks

    @ tasks.setter
    def tasks(self, value):
        if isinstance(value, list):
            self.add_tasks(value)
        elif isinstance(value, (UUID, Activity)):
            self._add_task(value)
        else:
            raise TypeError(
                f'Expected either a list of values or a single value of type {type(UUID)} or {type(Activity)}. Got {type(value)} = {repr(value)}.')

    def add_tasks(self, value: list):
        if not isinstance(value, list):
            raise TypeError(
                f'Expected a list but got {type(value)} = {repr(value)}.')
        for v in value:
            self._add_task(v)

    def remove_tasks(self, value: list):
        if not isinstance(value, (UUID, Activity)):
            raise TypeError(
                f'Expected value of type {UUID} or {Activity} but got {type(value)} = {repr(value)}')
        id = value
        if isinstance(value, Activity):
            id = value.id
        self._tasks.remove(id.hex)

    def _add_task(self, value):
        if not isinstance(value, (UUID, Activity, str)):
            raise TypeError(
                f'Expected value of type {UUID}, {Activity}, or {str} but got {type(value)} = {repr(value)}')
        id = value
        if isinstance(value, Activity):
            id = value.id.hex
        elif isinstance(value, UUID):
            id = value.hex
        self._tasks.add(id)

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
        attrs = [a for a in dir(self) if a not in ['_id', '_due', '_not_before'] and a.startswith(
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
        if not self.complete:
            return
        if self.interval == 'quarter':
            kwargs = {'months': 3}
        elif self.interval == 'biweekly':
            kwargs = {'weeks': 2}
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
