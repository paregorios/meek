#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the meek activity module."""

import logging
from meek.activity import Activity
from nose.tools import assert_equal, assert_false, assert_true, raises
from pathlib import Path
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

    def test_not_before(self):
        s = 'October 20, 2067'
        t = '2067-10-20'
        kwargs = {
            'title': 'test activity',
            'not_before': s
        }
        a = Activity(**kwargs)
        assert_equal(t, a.not_before)
