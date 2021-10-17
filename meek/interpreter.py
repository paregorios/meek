#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command interpreter for meek
"""

from inspect import getdoc
import logging
from meek.manager import Manager, UsageError
from pathlib import Path
import readline

WHERE_DEFAULT = '~/.meek'

logger = logging.getLogger(__name__)


class Interpreter:

    def __init__(self):
        self.manager = Manager()
        self.verbs = [a[6:] for a in dir(self) if a.startswith('_verb_')]
        self.aliases = {
            '?': 'help',
            'all': 'list',
            'done': 'complete',
            'h': 'help',
            'ls': 'list',
            'q': 'quit'
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
        msg = getattr(self, f'_verb_{verb}')(args, **kwargs)
        if msg is not None:
            return msg
        else:
            return ''

    def _objectify(self, objects):
        args = []
        kwargs = {}
        for o in objects:
            k = None
            for delim in [':', '=']:
                if delim in o:
                    parts = o.split(delim)
                    k = parts[0]
                    try:
                        v = parts[1]
                    except IndexError:
                        v = None
                    else:
                        if ',' in v:
                            v = v.split(',')
                    kwargs[k] = v
                    break
            if k is None:
                args.append(o)
        return (args, kwargs)

    def _uerror(self, verb: str, exception: Exception):
        """Handle usage error."""
        msg = str(exception)
        print(f'Error: {msg}')
        self._usage(verb)

    def _usage(self, verb):
        """Print usage for indicated command"""
        usage = getdoc(getattr(self, f'_verb_{verb}')).splitlines()[1:]
        return '\n'.join(usage)

    def _verb_complete(self, args, **kwargs):
        """
        Mark activities as complete.
        Requires a context (i.e., first do "list", "overdue", etc.)
        > complete 1
        > complete 3-4
        """
        try:
            return self.manager.complete_activity(args, **kwargs)
        except UsageError as err:
            self._uerror('complete', err)

    def _verb_debug(self, args, **kwargs):
        """
        Change logging level to DEBUG
        """
        logging.getLogger().setLevel(level=logging.DEBUG)
        return self._verb_level(args, **kwargs)

    def _verb_due(self, args, **kwargs):
        """
        List unfinished activities by due date.
            > due
            > due today
            > due tomorrow
            > due this week
            > due next month
        """
        qualifier = ' '.join(args)
        return self.manager.list_due(qualifier)

    def _verb_error(self, args, **kwargs):
        """
        Change logging level to ERROR
        """
        logging.getLogger().setLevel(level=logging.ERROR)
        return self._verb_level(args, **kwargs)

    def _verb_full(self, args, **kwargs):
        """
        Display all information for indicated activities.
        """
        return self.manager.display_full_activities(args, **kwargs)

    def _verb_help(self, args, **kwargs):
        """
        Get help with available commands.
            > help (lists all available command verbs)
            > help {verb} (prints usage for the indicated verb)
        """
        if args:
            verb = ' '.join(args)
            try:
                msg = getdoc(getattr(self, f'_verb_{verb}'))
            except AttributeError:
                msg = f'Error: Unrecognized verb {verb}. Try "help" to get a list of verbs.'
            return msg
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

    def _verb_info(self, args, **kwargs):
        """
        Change logging level to INFO
        """
        logging.getLogger().setLevel(level=logging.INFO)
        return self._verb_level(args, **kwargs)

    def _verb_level(self, args, **kwargs):
        """
        Get the current logging level.
        """
        levels = {
            logging.DEBUG: 'DEBUG',
            logging.INFO: 'INFO',
            logging.WARNING: 'WARNING',
            logging.ERROR: 'ERROR'
        }
        val = levels[logging.root.level]
        return f'Logging level is now {val}'

    def _verb_list(self, args, **kwargs):
        """
        List activities.
            > list
            > list eat
            > list tags:daily
            > list tags:daily due:today
            > list overdue
        """
        if args:
            try:
                kwargs['words']
            except KeyError:
                kwargs['words'] = args
            else:
                kwargs['words'] = list(set(args).update(kwargs['words']))
        return self.manager.list_activities(**kwargs)

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

    def _verb_modify(self, args, **kwargs):
        """
        Make modifications to selected activities.
            > modify 0 title:'go to the beach'
            > modify 1-3 due:tomorrow
            > modify 7-8 complete
            > modify 2 tags:
              (clears tags)
            > modify 2 tags:fish
            > modify 3 tags:cat,dog
        """
        try:
            return self.manager.modify_activity(args, **kwargs)
        except UsageError as err:
            self._uerror('modify', err)

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
            > new Take a nap due:'next monday'
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

    def _verb_overdue(self, args, **kwargs):
        """
        List unfinished activities by due date (including those previously due)
            > overdue
            > overdue today
            > overdue tomorrow
            > overdue this week
            > overdue next month
        """
        qualifier = ' '.join(args)
        return self.manager.list_due(qualifier, include_overdue=True)

    def _verb_purge(self, args, **kwargs):
        """
        Clear all activities and indexes.
            > purge
        """
        return self.manager.purge()

    def _verb_quit(self, args, **kwargs):
        """
        Quit interactive interface.
            > quit
            WARNING: unsaved data will be lost (use "save" first)
        """
        exit()

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

    def _verb_warning(self, args, **kwargs):
        """
        Change logging level to WARNING
        """
        logging.getLogger().setLevel(logging.WARNING)
        return self._verb_level(args, **kwargs)
