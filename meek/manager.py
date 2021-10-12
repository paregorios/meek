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
        pass

    def save_activities(self, where: pathlib.Path):
        if not where.is_dir():
            if where.exists():
                raise IOError(f'{where} exists and is not a directory')
            else:
                where.mkdir(parents=True)
        backup_dir = where / '.bak'
        shutil.rmtree(backup_dir, ignore_errors=True)
        backup_dir.mkdir()
        for p in where.iterdir():
            if p.is_file():
                shutil.move(p, backup_dir / p.name)
        for aid, adata in self.activities.items():
            with open(where / f'{aid}.json', 'w', encoding='utf-8') as f:
                json.dump(adata.asdict(), f, ensure_ascii=False, indent=4)
            del f
        return f'Wrote {len(self.activities)} JSON files at {where}.'
