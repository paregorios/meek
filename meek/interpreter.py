#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command interpreter for meek
"""

import logging
from meek.manager import Manager
import readline


logger = logging.getLogger(__name__)


class Interpreter:

    def __init__(self):
        self.manager = Manager()
        self.verbs = [a[6:] for a in dir(self) if a.startswith('_verb_')]

    def parse(self, parts):
        verb = parts[0]
        try:
            objects = parts[1:]
        except IndexError:
            objects = []
        if verb not in self.verbs:
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

    def _verb_new(self, args, **kwargs):
        return f'New! "{args}" "{kwargs}"'

    def _verb_quit(self, objects):
        """Quit interactive interface."""
        exit()
