#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for meek
"""

from airtight.cli import configure_commandline
from meek.interpreter import Interpreter
from meek.norm import norm
import logging
import shlex


logger = logging.getLogger(__name__)

DEFAULT_LOG_LEVEL = logging.WARNING
OPTIONAL_ARGUMENTS = [
    ['-l', '--loglevel', 'NOTSET',
        'desired logging level (' +
        'case-insensitive string: DEBUG, INFO, WARNING, or ERROR',
        False],
    ['-v', '--verbose', False, 'verbose output (logging level == INFO)',
        False],
    ['-w', '--veryverbose', False,
        'very verbose output (logging level == DEBUG)', False],
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
]


def interact():
    i = Interpreter()
    while True:
        try:
            s = norm(input('> '))
        except KeyboardInterrupt:
            i.parse('quit')
        parts = shlex.split(s)
        result = i.parse(parts)
        print(result)


def main(**kwargs):
    """
    main function
    """
    # logger = logging.getLogger(sys._getframe().f_code.co_name)
    interact()


if __name__ == "__main__":
    main(**configure_commandline(
        OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL))
