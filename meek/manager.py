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

    def add_activity(self, activity):
        """ Add an activity to the manager. """
        self.activities[activity.id.hex] = activity
        # indexing tbd
        return activity

    def new_activity(self, **kwargs):
        """ Create a new activity and add it to the manager. """
        a = Activity(**kwargs)
        a = self.add_activity(a)
        self.previous.append(a)
        return f'Added {repr(a)}.'

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
