#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command interpreter for meek
"""

from inspect import getdoc
import logging
from meek.manager import Manager, UsageError
from pathlib import Path
from pprint import pprint
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
            'bump': 'reschedule',
            'c': 'complete',
            'del': 'delete',
            'done': 'complete',
            'h': 'help',
            'ls': 'list',
            'm': 'modify',
            'n': 'new',
            '!': 'overdue',
            'q': 'quit',
            'rm': 'delete',
            's': 'save'
        }
        self.reverse_aliases = {}
        for a, v in self.aliases.items():
            try:
                self.reverse_aliases[v]
            except KeyError:
                self.reverse_aliases[v] = list()
            finally:
                self.reverse_aliases[v].append(a)
        for v, aliases in self.reverse_aliases.items():
            aliases.sort()

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
                try:
                    self.manager.indexes['tags'][verb]
                except KeyError:
                    try:
                        self.manager.indexes['words'][verb]
                    except KeyError:
                        return f'Unrecognized verb "{verb}"'
                    else:
                        return self.manager.list_activities(words=verb)
                else:
                    return self.manager.list_activities(tags=verb)
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

    def _verb_delete(self, args, **kwargs):
        """
        Delete indicated activities.
            > delete 2
            > delete 3-5
        """
        try:
            return self.manager.delete_activity(args, **kwargs)
        except UsageError as err:
            self._uerror('delete', err)

    def _verb_due(self, args, **kwargs):
        """
        List unfinished activities by due date.
            > due
            > due today
            > due tomorrow
            > due this week
            > due next month
        """
        kwargs['due'] = ' '.join(args)
        return self._verb_list([], **kwargs)

    def _verb_dump(self, args, **kwargs):
        if isinstance(args, list):
            if len(args) == 1:
                if args[0] == 'indexes':
                    return self.manager.dump_indexes()
        raise NotImplementedError(args)

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
            else:
                try:
                    aliases = self.reverse_aliases[verb]
                except KeyError:
                    pass
                else:
                    aliases = ', '.join(aliases)
                    msg += f'\nAliases: {aliases}'
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
        Note: returns only incomplete activities by default. Try instead:
            > list complete:true
            > list complete:any
        """
        try:
            kwargs['complete']
        except KeyError:
            kwargs['complete'] = False
        if args:
            if 'overdue' in args:
                kwargs['overdue'] = 'today'
                args.remove('overdue')
            elif 'due' in args:
                kwargs['due'] = 'today'
                args.remove('due')
            elif 'complete' in args:
                kwargs['complete'] = True
                args.remove('complete')
            elif 'done' in args:
                kwargs['complete'] = True
                args.remove('done')
            elif 'completed' in args:
                kwargs['complete'] = True
                args.remove('completed')
            elif 'finished' in args:
                kwargs['complete'] = True
                args.remove('finished')
            elif 'incomplete' in args:
                kwargs['complete'] = False
            if len(args) > 0:
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
        kwargs['overdue'] = ' '.join(args)
        return self._verb_list([], **kwargs)

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

    def _verb_reschedule(self, args, **kwargs):
        """
        Reschedule a "due" activity.
        Requires a context (i.e., first do "list", "overdue", etc.)
        > reschedule 1
          increments due date by one day
        > reschedule 1 today
          i.e. modify 1 due:today
        > reschedule 2-3 tomorrow
        > reschedule 5 monday
        > reschedule 7 weeks:2
        """
        try:
            return self.manager.reschedule_activity(args, **kwargs)
        except UsageError as err:
            self._uerror('modify', err)

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
