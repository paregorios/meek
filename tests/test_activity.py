#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the meek activity module."""

import logging
import maya
from tzlocal import get_localzone
from meek.activity import Activity
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


class Test_Activity(TestCase):

    def setUp(self):
        """Change me"""
        pass

    def tearDown(self):
        """Change me"""
        pass

    def test_due(self):
        today = maya.when('today', str(get_localzone()))
        cases = {
            '2067-10-20': ['2067-10-20', 'October 20, 2067', '10/20/67', '10/20/2067'],
            today.iso8601().split('T')[0]: ['today'],
            today.add(days=1).iso8601().split('T')[0]: ['tomorrow'],
            today.subtract(days=1).iso8601().split('T')[0]: ['yesterday'],
            today.snap('@w').add(weeks=1).add(days=5).iso8601().split('T')[0]: ['next week'],
            maya.when(f'{str(today.year)}-{str(today.month)}-1').add(months=2).subtract(days=1).iso8601().split(
                'T')[0]: ['next month'],
            maya.when(f'{str(today.year)}-12-31').add(years=1).iso8601().split(
                'T')[0]: ['next year']
            # next week, month, quarter, year, etc.
        }
        days_of_week = ['monday', 'tuesday', 'wednesday',
                        'thursday', 'friday', 'saturday', 'sunday']
        for i, dow in enumerate(days_of_week):
            dow_num = i + 1  # why, maya, why?
            if dow_num > today.weekday:
                delta = dow_num - today.weekday
            else:
                delta = 7 - (today.weekday - dow_num)
            k = today.add(days=delta).iso8601().split('T')[0]
            v = dow
            try:
                cases[k]
            except KeyError:
                cases[k] = list()
            finally:
                cases[k].append(v)
        pprint(cases, indent=4)
        for k, vals in cases.items():
            for val in vals:
                kwargs = {'due': val}
                a = Activity(**kwargs)
                assert_equal(k, a.due)

    def test_not_before(self):
        s = 'October 20, 2067'
        t = '2067-10-20'
        kwargs = {
            'title': 'test activity',
            'not_before': s
        }
        a = Activity(**kwargs)
        assert_equal(t, a.not_before)


class Test_ActivityProject(TestCase):

    def test_true(self):
        a = Activity(project=True)
        assert_true(a.project)

    def test_true_string(self):
        a = Activity(project='true')
        assert_true(a.project)

    def test_false(self):
        a = Activity(project=False)
        assert_false(a.project)

    def test_false_string(self):
        a = Activity(project='false')
        assert_false(a.project)

    def test_true_to_false(self):
        a = Activity(project='true')
        assert_true(a.project)
        a.project = False
        assert_false(a.project)

    def test_false_to_true(self):
        a = Activity(project='false')
        assert_false(a.project)
        a.project = True
        assert_true(a.project)
