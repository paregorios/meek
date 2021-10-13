#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command interpreter for meek
"""

from inspect import getdoc
import logging
from meek.manager import Manager
from pathlib import Path
import readline

WHERE_DEFAULT = '~/.meek'

logger = logging.getLogger(__name__)


class Interpreter:

    def __init__(self):
        self.manager = Manager()
        self.verbs = [a[6:] for a in dir(self) if a.startswith('_verb_')]
        self.aliases = {
            'q': 'quit',
            'h': 'help',
            '?': 'help'
        }

    def parse(self, parts):
        verb = parts[0]
        try:
            objects = parts[1:]
        except IndexError:
            objects = []
        if verb not in self.verbs:
            try:
                verb = self.aliases[verb]
            except KeyError:
                return f'Unrecognized verb "{verb}"'
        args, kwargs = self._objectify(objects)
        return getattr(self, f'_verb_{verb}')(args, **kwargs)

    def _objectify(self, objects):
        args = []
        kwargs = {}
        for o in objects:
            k = None
            for delim in [':', '=']:
                if delim in o:
                    parts = o.split(delim)
                    if len(parts) != 2:
                        raise RuntimeError(o)
                    k = parts[0]
                    v = parts[1]
                    if ',' in v:
                        v = v.split(',')
                    kwargs[k] = v
                    break
            if k is None:
                args.append(o)
        return (args, kwargs)

    def _usage(self, verb):
        """Print usage for indicated command"""
        usage = getdoc(getattr(self, f'_verb_{verb}')).splitlines()[1:]
        return '\n'.join(usage)

    def _verb_purge(self, args, **kwargs):
        """
        Clear all activities and indexes.
            > purge
        """
        return self.manager.purge()

    def _verb_help(self, args, **kwargs):
        """
        Get help with available commands.
            > help (lists all available command verbs)
            > help {verb} (prints usage for the indicated verb)
        """
        if args:
            return self._usage(' '.join(args))
        else:
            entries = [
                (
                    k.split('_')[-1],
                    getdoc(getattr(self, f'_verb_{k}')).splitlines()[0]
                ) for k in self.verbs]
            entries.sort(key=lambda x: x[0])
            longest = max([len(e[0]) for e in entries])
            entries = [f'{e[0]}:'.rjust(
                longest+1) + f' {e[1]}' for e in entries]
            return '\n'.join(entries)

    def _verb_load(self, args, **kwargs):
        """
        Load activities from storage.
            > load
              loads from default location
            > load my/favorite/directory
              loads from indicated path
        """
        if len(args) == 0:
            where = WHERE_DEFAULT
        elif len(args) == 1:
            where = args
        else:
            raise ValueError(args)
        where = Path(where).expanduser().resolve()
        return self.manager.load_activities(where)

    def _verb_new(self, args, **kwargs):
        """
        Create a new activity.
            > new
              creates a new, empty activity
            > new Take a nap
              creates a new activity with title "Take a nap"
            > new Take a nap due=today
            > new Take a nap due:today
            > new Take a nap due:2021-07-03
            > new Take a nap tags=personal,home,health
        """
        if len(args) > 0:
            try:
                kwargs['title']
            except KeyError:
                kwargs['title'] = ' '.join(args)
            else:
                raise ValueError(f'args: {args}, kwargs: {kwargs}')
        return self.manager.new_activity(**kwargs)

    def _verb_save(self, args, **kwargs):
        """
        Save activities to storage.
            > save
              saves to default location
            > save my/favorite/directory
              saves to indicated path
              WARNING: deletes existing content
        """
        if len(args) == 0:
            where = WHERE_DEFAULT
        elif len(args) == 1:
            where = args
        else:
            raise ValueError(args)
        where = Path(where).expanduser().resolve()
        return self.manager.save_activities(where)

    def _verb_quit(self, args, **kwargs):
        """
        Quit interactive interface.
            > quit
            WARNING: unsaved data will be lost (use "save" first)
        """
        exit()
