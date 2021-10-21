#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test dates module"""

from copy import copy
import logging
import math
import maya
from meek.dates import comprehend_date, iso_datestamp, tz
from nose.tools import assert_equal, assert_false, assert_true, raises
from pathlib import Path
from pprint import pprint, pformat
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
        today = maya.when('today', tz)
        for k, v in dow.items():
            day = maya.when(k, tz)
            if day.weekday > today.weekday:
                day = day.add(weeks=1)
            daystamp = iso_datestamp(day)
            a, b = comprehend_date(k)
            assert_equal(daystamp, iso_datestamp(a))
            assert_equal(daystamp, iso_datestamp(b))

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
            day = maya.when(k, tz)
            if day.weekday > today.weekday:
                day = day.add(weeks=1)
            day = day.add(weeks=1)
            daystamp = iso_datestamp(day)
            start_dt, end_dt = comprehend_date(kk)
            assert_equal(daystamp, iso_datestamp(start_dt))

    def test_last_days_of_week(self):
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
            kk = f'last {k}'
            day = maya.when(k, tz)
            if day.weekday > today.weekday:
                day = day.add(weeks=1)
            day = day.subtract(weeks=1)
            daystamp = iso_datestamp(day)
            start_dt, end_dt = comprehend_date(kk)
            assert_equal(daystamp, iso_datestamp(start_dt))

    def test_relative_periods(self):
        today = maya.when('today', tz)
        monday = maya.when('monday', tz)
        friday = monday.add(days=4)
        quarters = dict()
        for month in range(1, 12):
            quarter = math.ceil(month/3)
            try:
                quarters[quarter]
            except KeyError:
                quarters[quarter] = list()
            finally:
                quarters[quarter].append(month)
        quarters_by_month = dict()
        for quarter, months in quarters.items():
            for month in months:
                quarters_by_month[month] = quarter
        quarter_dates = dict()
        for quarter in quarters:
            first_day = maya.when(
                f'{today.year}-{quarters[quarter][0]}-1', tz)
            last_day = first_day.add(months=3).subtract(days=1)
            quarter_dates[quarter] = (
                iso_datestamp(first_day),
                iso_datestamp(last_day)
            )
        this_quarter = quarters_by_month[today.month]
        this_quarter_year = str(today.year)
        next_quarter = this_quarter + 1
        next_quarter_year = today.year
        if next_quarter == 5:
            next_quarter = 1
            next_quarter_year += 1
        next_quarter_year = str(next_quarter_year)
        last_quarter = this_quarter - 1
        last_quarter_year = today.year
        if last_quarter == 0:
            last_quarter = 4
            last_quarter_year -= 1
        last_quarter_year = str(last_quarter_year)

        cases = {
            'this week': (
                iso_datestamp(monday),
                iso_datestamp(friday)
            ),
            'next week': (
                iso_datestamp(monday.add(weeks=1)),
                iso_datestamp(friday.add(weeks=1))
            ),
            'last week': (
                iso_datestamp(monday.subtract(weeks=1)),
                iso_datestamp(friday.subtract(weeks=1))
            ),
            'this month': (
                iso_datestamp(today.snap('@month')),
                iso_datestamp(today.add(months=1).snap(
                    '@month').subtract(days=1))
            ),
            'next month': (
                iso_datestamp(today.add(months=1).snap('@month')),
                iso_datestamp(today.add(months=2).snap(
                    '@month').subtract(days=1))
            ),
            'last month': (
                iso_datestamp(today.subtract(months=1).snap('@month')),
                iso_datestamp(today.snap('@month').subtract(days=1))
            ),
            'this quarter': (
                quarter_dates[this_quarter][0],
                quarter_dates[this_quarter][1]
            ),
            'next quarter': (
                quarter_dates[next_quarter][0].replace(
                    this_quarter_year, next_quarter_year),
                quarter_dates[next_quarter][1].replace(
                    this_quarter_year, next_quarter_year)
            ),
            'last quarter': (
                quarter_dates[last_quarter][0].replace(
                    this_quarter_year, last_quarter_year),
                quarter_dates[last_quarter][1].replace(
                    this_quarter_year, last_quarter_year)
            ),
            'this year': (
                iso_datestamp(today.snap('@year')),
                iso_datestamp(today.snap(
                    '@year').add(years=1).subtract(days=1))
            ),
            'next year': (
                iso_datestamp(today.snap('@year').add(years=1)),
                iso_datestamp(today.snap(
                    '@year').add(years=2).subtract(days=1))
            ),
            'last year': (
                iso_datestamp(today.snap('@year').subtract(years=1)),
                iso_datestamp(today.snap('@year').subtract(days=1))
            )

        }
        for q, expected in cases.items():
            start_dt, end_dt = comprehend_date(q)
            assert_equal(expected[0], iso_datestamp(start_dt)),
            assert_equal(expected[1], iso_datestamp(end_dt))
