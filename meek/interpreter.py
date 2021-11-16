#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command interpreter for meek
"""

from inspect import getdoc
import logging
import maya
from meek.manager import Manager, UsageError
from pathlib import Path
from pprint import pprint
import re
import readline

WHERE_DEFAULT = '~/.meek'

logger = logging.getLogger(__name__)
rx_numeric = re.compile(r'^(?P<numeric>\d+)$')
rx_numeric_range = re.compile(r'^(?P<start>\d+)\s*-\s*(?P<end>\d+)$')


class Interpreter:

    def __init__(self):
        self.manager = Manager()
        self.loaded = False
        self.modified = True
        self.verbs = [a[6:] for a in dir(self) if a.startswith('_verb_')]
        self.aliases = {
            '?': 'help',
            'all': 'list',
            'bump': 'reschedule',
            'c': 'complete',
            'del': 'delete',
            'done': 'complete',
            'h': 'help',
            'i': 'incorporate',
            'ls': 'list',
            'm': 'modify',
            'n': 'new',
            '!': 'overdue',
            'q': 'quit',
            'rm': 'delete',
            's': 'save',
            't': 'tasks'
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
                kwargs = dict()
                for k in ['tags', 'words']:
                    try:
                        self.manager.indexes[k][verb]
                    except KeyError:
                        pass
                    else:
                        kwargs[k] = verb
                if len(kwargs) == 0:
                    return f'Unrecognized verb "{verb}"'
                elif len(kwargs) > 1:
                    kwargs['or'] = list(kwargs.keys())
                return self.manager.list_activities(**kwargs)
        args, kwargs = self._objectify(objects)
        try:
            msg = getattr(self, f'_verb_{verb}')(args, **kwargs)
        except UsageError as err:
            msg = self._uerror(verb, err)
        if msg is not None:
            return msg
        else:
            return ''

    def _comprehend_args(self, args):
        """Deal with numeric arguments."""
        i = None
        j = None
        other = []
        if args:
            logger.debug(f'args: {repr(args)}')
            a = args[0]
            if len(args) > 1:
                other = args[1:]
            m = rx_numeric.match(a)
            if m:
                logger.debug(f'numeric match for {repr(a)}')
                i = int(m.group('numeric'))
            if m is None:
                m = rx_numeric_range.match(a)
                if m:
                    logger.debug(f'numeric range match for {repr(a)}')
                    i = int(m.group('start'))
                    j = int(m.group('end'))
                else:
                    other.insert(0, a)
        logger.debug(f'Results: i={i}, j={j}, other={repr(other)}')
        return (i, j, other)

    def _objectify(self, objects):
        args = []
        kwargs = {}
        logger.debug(f'objects: {repr(objects)}')
        for o in objects:
            k = None
            if not o.startswith('http'):
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
        logger.debug(f'args: {repr(args)}')
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
            result = self.manager.complete_activity(args, **kwargs)
        except UsageError as err:
            self._uerror('complete', err)
        else:
            self.modified = True
            return result

    def _verb_current(self, args, **kwargs):
        """
        List activities that are either (over)due this week or tagged 'active'
            > current
            > current project:true
            > current interval:any
              (includes interval:day, which is excluded by default)
        """
        return self.manager.list_current(**kwargs)

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
            result = self.manager.delete_activity(args, **kwargs)
        except UsageError as err:
            self._uerror('delete', err)
        else:
            self.modified = True
            return result

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
        """
        Utility function for dumping indices to command line
            > dump indexes
        """
        if isinstance(args, list):
            if len(args) >= 1:
                if args[0] == 'indexes':
                    return self.manager.dump_indexes(args)
        raise NotImplementedError(args)

    def _verb_error(self, args, **kwargs):
        """
        Change logging level to ERROR
        """
        logging.getLogger().setLevel(level=logging.ERROR)
        return self._verb_level(args, **kwargs)

    def _verb_full(self, args, **kwargs):
        """
        Display all information for indicated activities (requires context).
            > full 7
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

    def _verb_import(self, args, **kwargs):
        """
        Import activities from an external file.
            > import path/to/file
            > import path/to/file due:friday tags:personal
              (keyword arguments used here are applied to all imported activities)
        """
        result = None
        if len(args) == 0:
            self._uerror('import', 'Path to file required for import')
        elif len(args) > 1:
            self._uerror(
                'import', 'Too many arguments. Expected one (path to file).')
        else:
            result = self.manager.import_activities(args[0], **kwargs)
        self.modified = True
        return result

    def _verb_incorporate(self, args, **kwargs):
        """
        Incorporate one or more activities as tasks into a single tasks, which is or becomes a project.
            > incorporate 7 9
            > incorporate 6-8 9
            In the above examples, the first numeral or numeric range designates the activities that are to become the subordinate task(s) and the second numeral (9) represents the activity that is or becomes a project.
        """
        if not len(args) == 2 or len(kwargs) > 0:
            self._uerror('incorporate', 'invalid arguments')
        m = rx_numeric.match(args[0])
        if m:
            tasks = [int(m.group('numeric'))]
        else:
            m = rx_numeric_range.match(args[0])
            if m:
                tasks = [int(m.group('start')), int(m.group('end'))]
            else:
                self._uerror(
                    'incorporate', f'First argument expected numeral or numeric range. Got: {repr(args[0])}.')
        m = rx_numeric.match(args[1])
        if m:
            project = int(m.group('numeric'))
        else:
            self._uerror(
                'incorporate', f'Second argument expected numeral. Got: {repr(args[1])}.'
            )
        result = self.manager.incorporate_tasks_into_project(project, tasks)
        self.modified = True
        return result

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

    def _verb_later(self, args, **kwargs):
        """
        Mark activity/ies with a not_before time so they are temporarily hidden from listings.
            > later 7 1 hour
            > later 1-5 20 minutes
            > later 2
              (defaults to 1 hour)
        """
        i, j, other = self._comprehend_args(args)
        qty = 1
        unit = 'hour'
        units = ['minute', 'minutes', 'hour',
                 'hours', 'day', 'days', 'week', 'weeks']
        if other:
            if len(other) == 1:
                try:
                    qty = int(other[0])
                except TypeError:
                    if other[0] in units:
                        unit = other[0]
                    else:
                        self._uerror(
                            'later', f'Unsupported unit value "{other[0]}". Supported: {repr(units)}.')
                        return None
            elif len(other) == 2:
                try:
                    qty = int(other[0])
                except TypeError:
                    self._uerror(
                        'later', f'Expected integer value for first argument. Got {other[0]}.')
                    return None
                if other[1] in units:
                    unit = other[1]
                else:
                    self._uerror(
                        'later', f'Unsupported unit value "{other[1]}". Supported: {repr(units)}.')
                    return None
            else:
                self._uerror(
                    'later', f'Incorrect number of arguments: {len(other)}')
                return None
        else:
            unit = 'hours'
            qty = 1
        if not unit[-1] == 's':
            unit = f'{unit}s'
        now = maya.now()
        then = now.add(**{unit: qty})
        if j is None:
            m_arg = [f'{i}', ]
        else:
            m_arg = [f'{i}-{j}', ]
        return self.manager.modify_activity(
            m_arg, **{'not_before': then.iso8601()})

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
        result = self.manager.load_activities(where)
        m = re.match(
            r'^Loaded (\d+) activities from JSON files at .+$', result)
        if m is not None:
            if m.group(1) != '0':
                self.loaded = True
                self.modified = False
        return result

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
            result = self.manager.modify_activity(args, **kwargs)
        except UsageError as err:
            self._uerror('modify', err)
        else:
            self.modified = True
            return result

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
        try:
            result = self.manager.new_activity(**kwargs)
        except ValueError as err:
            self._uerror('new', err)
            return ''
        self.modified = True
        return result

    def _verb_notes(self, args, **kwargs):
        """
        Manipulate notes on an activity.
            > notes 7 add some note text
              (creates a note on context activity 7 with text 'some note text')
            > notes 7 list
              (lists any notes on context activity 7)
        """
        if len(args) < 2:
            self._uerror(
                'notes', f'Expected at least two 2 arguments, got {len(args)}.')
        else:
            i, j, other = self._comprehend_args(args)
            if not isinstance(i, int):
                self._uerror(
                    'notes', f'Expected numeral for first argument, but got {type(i)}={repr(i)}')
            elif j is not None:
                self._uerror(
                    'notes', f'Numeric ranges not supported. Notes can be added only to a single activity at a time.'
                )
            elif other[0] == 'add':
                return self.manager.add_note(i, ' '.join(other[1:]))
            elif other[0] == 'list':
                return self.manager.list_notes(i)
            else:
                self._uerror(
                    'notes', f'Expected "add" or "list" for second argument, but got {other[0]}'
                )

        return ''

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

    def _verb_projects(self, args, **kwargs):
        """
        List all projects
            > projects
            > projects stalled:true
            > projects due:'this month' stalled:false
        """
        kwargs['project'] = True
        return self._verb_list([], **kwargs)

    def _verb_purge(self, args, **kwargs):
        """
        Clear all activities and indexes.
            > purge
        """
        result = self.manager.purge()
        self.modified = False
        return result

    def _verb_quit(self, args, **kwargs):
        """
        Quit interactive interface.
            > quit
            WARNING: unsaved data will be lost (use "save" first)
        """
        if self.loaded and self.modified:
            allow = False
            try:
                f = kwargs['force']
            except KeyError:
                pass
            else:
                f = f.lower()
                if f == 'true':
                    allow = True
            if not allow:
                return 'Quitting without force:true not permitted unless you have first saved all changes.'
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
            result = self.manager.reschedule_activity(args, **kwargs)
        except UsageError as err:
            self._uerror('modify', err)
        else:
            self.modified = True
            return result

    def _verb_save(self, args, **kwargs):
        """
        Save activities to storage.
            > save
              saves to default location
            > save my/favorite/directory
              saves to indicated path
              WARNING: deletes existing content
        """
        if not self.loaded:
            allow = False
            try:
                f = kwargs['force']
            except KeyError:
                pass
            else:
                f = f.lower()
                if f == 'true':
                    allow = True
            if not allow:
                return 'Saving without force:true not permitted if you have not first loaded.'
        if len(args) == 0:
            where = WHERE_DEFAULT
        elif len(args) == 1:
            where = args
        else:
            raise ValueError(args)
        where = Path(where).expanduser().resolve()
        result = self.manager.save_activities(where)
        self.modified = False
        return result

    def _verb_stalled(self, args, **kwargs):
        """
        List stalled projects (i.e., those without any associated subtasks)
            > stalled
            > stalled due:'this quarter'
        """
        kwargs['stalled'] = 'True'
        return self._verb_projects(args, **kwargs)

    def _verb_tasks(self, args, **kwargs):
        """
        List all the tasks associated with a particular project that's in context.
            > tasks 7
        """
        if len(kwargs) != 0:
            raise ValueError(kwargs)
        i, j, other = self._comprehend_args(args)
        if j is not None or len(other) != 0:
            raise ValueError(args)
        return self.manager.show_tasks(i)

    def _verb_today(self, args, **kwargs):
        """
        List activities that are either overdue as of today or tagged 'active'
            > today
            > today project:true
        Unlike "current", interval:any is included by default
        """
        try:
            kwargs['interval']
        except KeyError:
            kwargs['interval'] = 'any'  # override defaults in list_current
        try:
            kwargs['overdue']
        except KeyError:
            kwargs['overdue'] = 'today'
        return self.manager.list_current(**kwargs)

    def _verb_tomorrow(self, args, **kwargs):
        """
        List activities that are either overdue as of tomorrow or tagged 'active'
            > tomorrow
            > tomorrow project:true
        Unlike "current", interval:any is included by default
        """
        try:
            kwargs['interval']
        except KeyError:
            kwargs['interval'] = 'any'  # override defaults in list_current
        try:
            kwargs['overdue']
        except KeyError:
            kwargs['overdue'] = 'tomorrow'
        return self.manager.list_current(**kwargs)

    def _verb_warning(self, args, **kwargs):
        """
        Change logging level to WARNING
        """
        logging.getLogger().setLevel(logging.WARNING)
        return self._verb_level(args, **kwargs)
