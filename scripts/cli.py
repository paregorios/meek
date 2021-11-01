#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for meek
"""

from re import A
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
    while True:  # keep taking commands until something breaks us out to finish the program
        try:
            s = norm(input('> '))
        except KeyboardInterrupt:
            i.parse('quit')
        while True:  # try to fix common errors and re-parse
            parts = list()
            try:
                parts = shlex.split(s)
            except ValueError as err:
                msg = str(err)
                if s[0:4] == 'new ':
                    if s[4] == '"' and s[-1] == "'" and len([c for c in s[4:] if c == "'"]) % 2 == 0:
                        foo = list(s)
                        foo[-1] = '"'
                        s = ''.join(foo)
                else:
                    logger.error(f'ValueError: {msg}')
                    break  # need new input
                continue  # try to split corrected string
            if parts:
                result = i.parse(parts)
                if result:
                    print(result)
            break


def main(**kwargs):
    """
    main function
    """
    # logger = logging.getLogger(sys._getframe().f_code.co_name)
    interact()


if __name__ == "__main__":
    main(**configure_commandline(
        OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL))
