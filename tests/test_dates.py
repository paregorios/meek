#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test dates module"""

from copy import copy
import logging
import maya
from meek.dates import comprehend_date, iso_datestamp, tz
from nose.tools import assert_equal, assert_false, assert_true, raises
from pathlib import Path
from pprint import pprint
from unittest import TestCase

logger = logging.getLogger(__name__)
test_data_path = Path('tests/data').resolve()


def setup_module():
    """Change me"""
    pass


def teardown_module():
    """Change me"""
    pass


class Test_Dates(TestCase):

    def setUp(self):
        """Change me"""
        pass

    def tearDown(self):
        """Change me"""
        pass

    def test_blank(self):
        s = ''
        a, b = comprehend_date(s)
        today = maya.now()
        for k in ['year', 'month', 'day']:
            assert_equal(getattr(today, k), getattr(a, k))
            assert_equal(getattr(a, k), getattr(b, k))

    def test_today(self):
        s = 'today'
        a, b = comprehend_date(s)
        today = maya.now()
        for k in ['year', 'month', 'day']:
            assert_equal(getattr(today, k), getattr(a, k))
            assert_equal(getattr(a, k), getattr(b, k))

    def test_yesterday(self):
        s = 'yesterday'
        a, b = comprehend_date(s)
        when = maya.now().subtract(days=1)
        for k in ['year', 'month', 'day']:
            assert_equal(getattr(when, k), getattr(a, k))
            assert_equal(getattr(a, k), getattr(b, k))

    def test_tomorrow(self):
        s = 'tomorrow'
        a, b = comprehend_date(s)
        when = maya.now().add(days=1)
        for k in ['year', 'month', 'day']:
            assert_equal(getattr(when, k), getattr(a, k))
            assert_equal(getattr(a, k), getattr(b, k))

    def test_days_of_week(self):
        dow = {
            'monday': 1,
            'tuesday': 2,
            'wednesday': 3,
            'thursday': 4,
            'friday': 5,
            'saturday': 6,
            'sunday': 7
        }
        when = maya.now()
        for k, v in dow.items():
            a, b = comprehend_date(k)
            if v == when.weekday:
                then = copy(when)
            elif v < when.weekday:
                delta = when.weekday - v
                then = when.subtract(days=delta)
            else:
                delta = v - when.weekday
                then = when.add(days=delta)
            for attrname in ['year', 'month', 'day']:
                x = getattr(then, attrname)
                y = getattr(a, attrname)
                print(f'then.{attrname}: {x}')
                print(f'a.{attrname}: {y}')
                assert_equal(x, y)
                # assert_equal(getattr(a, k), getattr(b, k))

    def test_days_of_week(self):
        dow = {
            'monday': 1,
            'tuesday': 2,
            'wednesday': 3,
            'thursday': 4,
            'friday': 5,
            'saturday': 6,
            'sunday': 7
        }
        when = maya.now()
        for k, v in dow.items():
            a, b = comprehend_date(k)
            if v == when.weekday:
                then = copy(when)
            elif v < when.weekday:
                delta = when.weekday - v
                then = when.subtract(days=delta)
            else:
                delta = v - when.weekday
                then = when.add(days=delta)
            for attrname in ['year', 'month', 'day']:
                x = getattr(then, attrname)
                y = getattr(a, attrname)
                assert_equal(x, y)

    def test_next_days_of_week(self):
        dow = {
            'monday': 1,
            'tuesday': 2,
            'wednesday': 3,
            'thursday': 4,
            'friday': 5,
            'saturday': 6,
            'sunday': 7
        }
        today = maya.when('today', tz)
        for k, v in dow.items():
            kk = f'next {k}'
            start_dt, end_dt = comprehend_date(kk)
            expected_dt = today.add(weeks=1)
            assert_equal(
                iso_datestamp(expected_dt),
                iso_datestamp(start_dt)
            )

    def test_relative_periods(self):
        today = maya.when('today', tz)
        monday = maya.when('monday', tz)
        friday = monday.add(days=4)
        cases = {
            'this week': (
                iso_datestamp(monday),
                iso_datestamp(friday)
            ),
            'next week': (
                iso_datestamp(monday.add(weeks=1)),
                iso_datestamp(friday.add(weeks=1))
            )
        }
        pprint(cases, indent=4)
        for q, expected in cases.items():
            start_dt, end_dt = comprehend_date(q)
            print(q)
            print('start')
            assert_equal(expected[0], iso_datestamp(start_dt)),
            print('end')
            assert_equal(expected[1], iso_datestamp(end_dt))
