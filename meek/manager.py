#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manager for meek
"""

from collections import deque
from copy import copy
from meek.dates import comprehend_date, iso_datestamp
import json
import logging
import maya
from meek.activity import Activity
from meek.dates import comprehend_date
import pathlib
from pprint import pformat, pprint
import re
import shutil
from tzlocal import get_localzone


logger = logging.getLogger(__name__)
rx_numeric = re.compile(r'^(?P<numeric>\d+)$')
rx_numeric_range = re.compile(r'^(?P<start>\d+)\s*-\s*(?P<end>\d+)$')


class UsageError(Exception):

    def __init__(self, message: str = ''):
        self.message = message
        super().__init__(self.message)


class Manager:

    def __init__(self):
        self.activities = dict()
        self.previous = deque()
        self.current = list()
        self.indexes = {
            'title': {},
            'words': {},
            'tags': {},
            'due': {},
            'complete': {},
            'not_before': {}
        }
        self.reverse_index = {}

    def add_activity(self, activity):
        """ Add an activity to the manager. """
        self.activities[activity.id.hex] = activity
        self._index_activity(activity)
        return activity

    def complete_activity(self, args, **kwargs):
        context = self.current
        if len(context) == 0:
            context = list(self.previous)
        if len(context) == 0:
            raise UsageError(
                'No activity context is defined. First use "list", "due", "overdue" or another similar command.')
        i = None
        j = None
        if args:
            v = ' '.join(args)
            m = rx_numeric.match(v)
            if m:
                i = int(m.group('numeric'))
            if m is None:
                m = rx_numeric_range.match(v)
                if m:
                    i = int(m.group('start'))
                    j = int(m.group('end')) + 1
                else:
                    raise UsageError(f'Unrecognized argument {repr(v)}')
        else:
            raise UsageError(f'Missing argument: number or numeric range.')
        for n in [i, j]:
            if n is not None:
                try:
                    context[i]
                except IndexError:
                    msg = f'Numeric argument {n} is out of range in current context. Valid range is 0-{len(context)-1}.'
                    raise UsageError(msg)
        alist = [context[i]]
        if j is not None:
            alist = context[i:j]
        for a in alist:
            a.complete = True
        self._index_activity(a)
        if len(alist) == 1:
            msg = f'Marked 1 activity as completed.'
        else:
            msg = f'Marked {len(alist)} activities as completed.'
        return msg

    def delete_activity(self, args, **kwargs):
        """ Delete an existing activity. """
        i, j, other = self._comprehend_args(args)
        if i is None:
            raise UsageError(
                'The first argument must be a number or numeric range.')
        if other:
            raise UsageError(
                f'Unexpected additional arguments: {repr(other)}.')
        alist = self._contextualize(i, j)
        id_list = [a.id for a in alist]
        for id in id_list:
            self.activities.pop(id.hex)
        if len(id_list) == 1:
            return 'Deleted 1 activity.'
        else:
            return f'Deleted {len(id_list)} activities.'

    def display_full_activities(self, args, **kwargs):
        if args:
            v = ' '.join(args)
            if v in ['last', 'previous']:
                return self.display_full_activity(-1)
            elif v == 'all':
                context = self.current
                if len(context) == 0:
                    context = list(self.previous)
                msg = []
                for i in range(0, len(context)):
                    msg.append(self.display_full_activity(i))
                msg = '\n'.join(msg)
                return msg
            elif v == 'first':
                return self.display_full_activity(0)
            m = rx_numeric.match(v)
            if m:
                return self.display_full_activity(int(m.group('numeric')))
            m = rx_numeric_range.match(v)
            if m:
                msg = []
                for i in range(int(m.group('start')), int(m.group('end')) + 1):
                    msg.append(self.display_full_activity(i))
                msg = '\n'.join(msg)
                return msg
            logger.error(f'Unrecognized argument "{v}".')
            return ''
        else:
            return self.display_full_activity()

    def display_full_activity(self, sequence=None):
        if len(self.current) == 0:
            context = list(self.previous)
        else:
            context = self.current
        if sequence is not None:
            try:
                a = context[sequence]
            except IndexError:
                logger.error(
                    f'Sequence number {sequence} is not in current context.')
                return self.list_activities()
        else:
            try:
                a = context[-1]
            except IndexError:
                logger.error(
                    'No activity context is defined. Try the "list" command first.')
                return ''
        d = a.asdict()
        return pformat(d, indent=4, sort_dicts=True)

    def dump_indexes(self):
        msg = []
        msg.append(pformat(self.indexes, indent=4))
        msg.append(pformat(self.reverse_index, indent=4))
        return '\n'.join(msg)

    def list_activities(self, **kwargs):
        alist = self._get_list(**kwargs)
        try:
            sortkeys = kwargs['sort']
        except KeyError:
            out_list = self._format_list(alist)
        else:
            out_list = self._format_list(alist, sort=sortkeys)
        self.current = alist
        return '\n'.join(out_list)

    def load_activities(self, where: pathlib.Path):
        activity_dir = where / 'activities'
        i = 0
        for p in activity_dir.iterdir():
            if p.is_file():
                if p.name.endswith('.json'):
                    with open(p, 'r', encoding='utf-8') as f:
                        adict = json.load(f)
                    del f
                    a = Activity(**adict, mode='memorex')
                    self.add_activity(a)
                    i += 1
        return f'Loaded {i} activities from JSON files at {where}.'

    def modify_activity(self, args, **kwargs):
        """ Modify an existing activity. """
        i, j, other = self._comprehend_args(args)
        if i is None:
            raise UsageError(
                'The first argument must be a number or numeric range.')
        alist = self._contextualize(i, j)
        if other:
            for val in other:
                if val in ['complete', 'done']:
                    kwargs['complete'] = True
                else:
                    raise UsageError(f'Unrecognized argument {repr(val)}.')
        for a in alist:
            for k, arg in kwargs.items():
                setattr(a, k, arg)
            self._index_activity(a)
        out_list = self._format_list(alist)
        self.current = alist
        msg = f'Modified {len(alist)} activities:\n'
        msg += '\n'.join(out_list)
        return msg

    def new_activity(self, **kwargs):
        """ Create a new activity and add it to the manager. """
        a = Activity(**kwargs)
        a = self.add_activity(a)
        self._apply_keywords(a)
        self.previous.append(a)
        return f'Added {repr(a)}.'

    def purge(self):
        count = len(self.activities)
        self.activities = dict()
        return f'Purged {count} activities from memory.'

    def reschedule_activity(self, args, **kwargs):
        """Change the due date on an activity."""
        i, j, other = self._comprehend_args(args)
        if i is None:
            raise UsageError(
                'The first argument must be a number or numeric range.')
        tz = str(get_localzone())
        alist = self._contextualize(i, j)
        success = 0
        for idx, a in enumerate(alist):
            if a.due is None:
                logger.error(
                    f'Activity {idx}:"{a.title}" has no due date. Reschedule command ignored.')
                continue
            due_dt = maya.when(a.due, tz)
            if len(other) == 0:
                if len(kwargs) == 0:
                    due_dt = due_dt.add(days=1)
                elif len(kwargs) == 1:
                    k = list(kwargs.keys())[0]
                    if k in ['days', 'weeks', 'months', 'years']:
                        due_dt = due_dt.add(**kwargs)
                    else:
                        raise NotImplementedError(f'kwargs={repr(kwargs)}')
                else:
                    raise NotImplementedError(f'kwargs={repr(kwargs)}')
            else:
                arg = ' '.join(other)
                start_dt, end_dt = comprehend_date(arg)
                if end_dt is not None:
                    due_dt = end_dt
                elif start_dt is not None:
                    due_dt = start_dt
                else:
                    raise NotImplementedError(f'arg={arg}')
            a.due = due_dt
            success += 1
        if len(alist) <= 1:
            noun = 'activity'
        else:
            noun = 'activities'
        if success == 0:
            msg = f'Unable to reschedule {len(alist)} {noun}.'
        else:
            msg = f'Rescheduled {success} out of {len(alist)} {noun}.'
        return msg

    def save_activities(self, where: pathlib.Path):
        if len(self.activities) == 0:
            return 'There are no loaded activities to save. Command ignored.'
        if where.exists():
            if not where.is_dir():
                raise IOError(f'{where} exists and is not a directory')
        else:
            where.mkdir(parents=True)
        backup_dir = where / '.bak'
        if backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=False)
        backup_dir.mkdir(exist_ok=True)
        for fsobj in where.iterdir():
            if not fsobj.name.startswith('.'):
                logger.info(f'moving {fsobj} to {backup_dir}')
                shutil.move(fsobj, backup_dir / fsobj.name)
        activity_dir = where / 'activities'
        activity_dir.mkdir()
        for aid, adata in self.activities.items():
            with open(activity_dir / f'{aid}.json', 'w', encoding='utf-8') as f:
                json.dump(adata.asdict(), f, ensure_ascii=False, indent=4)
            del f
        return f'Wrote {len(self.activities)} JSON files at {where}.'

    def _apply_keywords(self, activity):
        logger.debug(f'_apply_keywords: activity={repr(activity)}')
        keywords = {
            'annually': {
                'due': 'today',
                'interval': 'year'
            },
            'daily': {
                'due': 'today',
                'interval': 'day'
            },
            'medicate': {
                'tags': 'health'
            },
            'medicated': {
                'tags': 'health'
            },
            'medicine': {
                'tags': 'health'
            },
            'meds': {
                'tags': 'health',
            },
            'monthly': {
                'due': 'today',
                'interval': 'month'
            },
            'quarterly': {
                'due': 'today',
                'interval': 'quarter'
            },
            'weekly': {
                'due': 'today',
                'interval': 'week'
            },
            'yearly': {
                'due': 'today',
                'interval': 'year'
            },
        }
        awords = activity.words
        logger.debug(f'awords = {repr(awords)}')
        for kw, actions in keywords.items():
            if kw in awords:
                for attrname, value in actions.items():
                    if attrname in ['due']:
                        v = getattr(activity, attrname)
                        if v is not None:
                            continue
                    setattr(activity, attrname, value)

    def _contextualize(self, i, j):
        for context in [self.current, list(self.previous)]:
            if context:
                vals = [i, ]
                if j is not None:
                    vals.append(j)
                for n in vals:
                    try:
                        context[n]
                    except IndexError:
                        raise UsageError(
                            f'Supplied index {n} is not in context (0-{len(context)})')
                if j is None:
                    alist = [context[i], ]
                else:
                    alist = context[i:j]
                return alist

        raise UsageError(f'No activity context is defined.')

    def _comprehend_args(self, args):
        i = None
        j = None
        other = []
        if args:
            a = args[0]
            if len(args) > 1:
                other = args[1:]
            m = rx_numeric.match(a)
            if m:
                i = int(m.group('numeric'))
            if m is None:
                m = rx_numeric_range.match(a)
                if m:
                    i = int(m.group('start'))
                    j = int(m.group('end')) + 1
                else:
                    other.insert(0, a)
        return (i, j, other)

    def _filter_list(self, alist, idxname, argv):
        if idxname == 'not_before':
            return self._filter_list_not_before(alist, argv)
        elif idxname in ['due', 'overdue']:
            return self._filter_list_by_date(alist, idxname, argv)
        try:
            idx = self.indexes[idxname]
        except KeyError:
            raise NotImplementedError(idxname)
        if isinstance(argv, str):
            filtervals = [argv.lower(), ]
        elif isinstance(argv, list):
            filtervals = [val.lower() for val in argv]
        elif isinstance(argv, bool):
            filtervals = [argv, ]
        else:
            raise TypeError(f'argv: {type(argv)}={repr(argv)}')
        result = set(alist)
        for fv in filtervals:
            try:
                blist = idx[fv]
            except KeyError:
                blist = list()
            result = result.intersection(blist)
        return list(result)

    def _filter_list_by_date(self, alist, idxname, argv):
        try:
            idx = self.indexes[idxname]
        except KeyError:
            if idxname == 'overdue':
                idx = self.indexes['due']
            else:
                raise NotImplementedError(idxname)
        if isinstance(argv, str):
            val = argv
        elif isinstance(argv, list):
            if len(argv) > 1:
                raise ValueError(
                    f'Only 1 value is supported for filtering by {idxname}. Got {len(argv)} = {repr(argv)}.')
            else:
                val = argv[0]
        if val == '':
            val = 'today'
        start_dt, end_dt = comprehend_date(val)
        start = iso_datestamp(start_dt)
        try:
            end = iso_datestamp(end_dt)
        except TypeError:
            end = start
        if idxname == 'due' and end == start:
            try:
                blist = idx[start]
            except KeyError:
                blist = list()
        elif idxname == 'due':
            matches = [a for k, a in idx.items() if k >= start and k <= end]
            blist = [item for sublist in matches for item in sublist]
        elif idxname == 'overdue':
            matches = [a for k, a in idx.items() if k <= end]
            blist = [item for sublist in matches for item in sublist]
        result = set(alist)
        try:
            result = result.intersection(blist)
        except TypeError:
            pprint(blist, indent=4)
            raise
        return list(result)

    def _filter_list_not_before(self, alist, argv):
        if isinstance(argv, str):
            val = argv
        elif isinstance(argv, list):
            if len(argv) > 1:
                raise ValueError(
                    f'Only 1 value is supported for filtering by not_before. Got {len(argv)} = {repr(argv)}.')
            else:
                val = argv[0]
        if val == '':
            val = 'today'
        idx = self.indexes['not_before']
        start_dt, end_dt = comprehend_date(val)
        start = iso_datestamp(start_dt)
        matches = []
        for k, a in idx.items():
            if k <= start:
                matches.append(a)
        blist = [item for sublist in matches for item in sublist]
        blist.extend([a for a in self.activities.values()
                     if a.not_before is None])
        result = set(alist)
        result = result.intersection(blist)
        return list(result)

    def _filter_list_title(self, alist, filtervals):
        result = set(alist)
        for fv in filtervals:
            result = result.intersection(self.indexes['title'][fv])
        return list(result)

    def _format_list(self, alist, attributes=['title', 'due'], sort=['due', 'title']):
        if isinstance(sort, list):
            if sort:
                for sk in sort:
                    if sk not in attributes:
                        raise ValueError(
                            f'sort key "{sk}" not in attributes ({attributes})')
                alist.sort(key=lambda a: [getattr(a, sk)
                           for sk in sort if getattr(a, sk) is not None])
        elif sort is None:
            pass
        else:
            raise TypeError(f'sort: {type(sort)} = {repr(sort)}')

        out_list = list()
        for i, a in enumerate(alist):
            serial = f'{i}:'
            for j, attrname in enumerate(attributes):
                attrval = getattr(a, attrname)
                if attrval is None or not attrval:
                    continue
                if attrname == 'title':
                    if j == 0:
                        serial += f' "{attrval}"'
                    else:
                        serial += f' title:"{attrval}"'
                else:
                    serial += f' {attrname}:{attrval}'
            out_list.append(serial)
        return out_list

    def _get_list(self, **kwargs):
        alist = list(self.activities.values())
        if not kwargs:
            return self._filter_list_not_before(alist, 'today')
        try:
            c = kwargs['complete']
        except KeyError:
            kwargs['complete'] = False
        else:
            if isinstance(c, bool):
                pass
            elif isinstance(c, str):
                c = c.lower()
                if c in ['false', 'f']:
                    kwargs['complete'] = False
                elif c in ['true', 't']:
                    kwargs['complete'] = True
                elif c in ['any', 'all']:
                    kwargs.pop('complete')
                else:
                    raise ValueError(
                        f'Unexpected value for "complete": "{repr(c)}".')
            else:
                raise TypeError(
                    f'Unexpected type for "complete": {type(c)} = "{repr(c)}".'
                )
        try:
            nb = kwargs['not_before']
        except KeyError:
            alist = self._filter_list_not_before(alist, 'today')
        else:
            if nb in ['any', 'all']:
                kwargs.pop('not_before')
        for k, argv in kwargs.items():
            if k == 'sort':
                continue
            alist = self._filter_list(alist, k, argv)
        return alist

    def _index_activity(self, activity):
        try:
            self.reverse_index[activity.id]
        except KeyError:
            self.reverse_index[activity.id] = {}
        finally:
            ridx = self.reverse_index[activity.id]
        for idxk, idx in self.indexes.items():
            try:
                ridx[idxk]
            except KeyError:
                ridx[idxk] = list()
            else:
                for val in ridx[idxk]:
                    idx[val].remove(activity)
                    if len(idx[val]) == 0:
                        idx.pop(val)
                ridx[idxk] = list()
            finally:
                ridx_sub = ridx[idxk]
            try:
                v = getattr(activity, idxk)
            except AttributeError:
                logger.error(f'indexable attribute not found: {idxk}')
            else:
                if v is None:
                    continue
                elif isinstance(v, str):
                    vals = [v.lower(), ]
                elif isinstance(v, (list, set)):
                    vals = [val.lower() for val in v]
                elif isinstance(v, bool):
                    vals = [v, ]
                elif isinstance(v, maya.MayaDT):
                    vals = [v.iso8601(), ]
                else:
                    raise TypeError(f'v: {type(v)}={repr(v)}')
                for v in vals:
                    try:
                        idx[v]
                    except KeyError:
                        idx[v] = list()
                    finally:
                        idx[v].append(activity)
                        ridx_sub.append(v)
