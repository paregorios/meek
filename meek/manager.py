#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manager for meek
"""

from collections import deque
import json
import logging
from meek.activity import Activity
import pathlib
import shutil

logger = logging.getLogger(__name__)


class Manager:

    def __init__(self):
        self.activities = dict()
        self.previous = deque()
        self.current = list()
        self.indexes = {
            'title': {},
            'words': {}
        }

    def add_activity(self, activity):
        """ Add an activity to the manager. """
        self.activities[activity.id.hex] = activity
        self._index_activity(activity)
        return activity

    def _index_activity(self, activity):
        for idxk, idx in self.indexes.items():
            try:
                v = getattr(activity, idxk)
            except AttributeError:
                logger.error(f'indexable attribute not found: {idxk}')
            else:
                if isinstance(v, str):
                    vals = [v, ]
                elif isinstance(v, (list, set)):
                    vals = v
                else:
                    raise TypeError(f'v: {type(v)}={repr(v)}')
                for v in [val.lower() for val in vals]:
                    try:
                        idx[v]
                    except KeyError:
                        idx[v] = list()
                    finally:
                        idx[v].append(activity)

    def new_activity(self, **kwargs):
        """ Create a new activity and add it to the manager. """
        a = Activity(**kwargs)
        a = self.add_activity(a)
        self.previous.append(a)
        return f'Added {repr(a)}.'

    def _filter_list_title(self, alist, filtervals):
        result = set(alist)
        for fv in filtervals:
            result = result.intersection(self.indexes['title'][fv])
        return list(result)

    def _filter_list(self, alist, idxname, argv):
        if isinstance(argv, str):
            filtervals = [argv, ]
        elif isinstance(argv, list):
            filtervals = argv
        else:
            raise TypeError(f'argv: {type(argv)}={repr(argv)}')
        result = set(alist)
        for fv in [v.lower() for v in filtervals]:
            idx = self.indexes[idxname]
            try:
                blist = idx[fv]
            except KeyError:
                blist = list()
            result = result.intersection(blist)
        return list(result)

    def _get_list(self, **kwargs):
        alist = list(self.activities.values())
        if not kwargs:
            return alist
        for k, argv in kwargs.items():
            if k == 'sort':
                continue
            alist = self._filter_list(alist, k, argv)
        return alist

    def list_activities(self, **kwargs):
        alist = self._get_list(**kwargs)
        try:
            sortkeys = kwargs['sort']
        except KeyError:
            alist.sort(key=lambda a: a.title)
        else:
            if isinstance(sortkeys, str):
                alist.sort(key=lambda a: getattr(a, sortkeys))
            elif isinstance(sortkeys, list):
                alist.sort(key=lambda a: [getattr(a, sk) for sk in sortkeys])
        self.current = alist
        return '\n'.join([f'{i}: {repr(a)}' for i, a in enumerate(alist)])

    def load_activities(self, where: pathlib.Path):
        activity_dir = where / 'activities'
        i = 0
        for p in activity_dir.iterdir():
            if p.is_file():
                if p.name.endswith('.json'):
                    with open(p, 'r', encoding='utf-8') as f:
                        adict = json.load(f)
                    del f
                    a = Activity(**adict)
                    self.add_activity(a)
                    i += 1
        return f'Loaded {i} activities from JSON files at {where}.'

    def purge(self):
        count = len(self.activities)
        self.activities = dict()
        return f'Purged {count} activities from memory.'

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
