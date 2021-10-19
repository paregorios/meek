#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test dates module"""

import logging
import maya
from meek.dates import comprehend_date
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
