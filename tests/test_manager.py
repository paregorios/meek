#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python 3 tests template (changeme)"""

import logging
from meek.manager import Manager
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


class Test_This(TestCase):

    def setUp(self):
        """Change me"""
        pass

    def tearDown(self):
        """Change me"""
        pass

    def test_a(self):
        """Change me"""
        pass


class Test_Activity(TestCase):

    def test_new_task(self):
        m = Manager()
        m.new_activity(
            title='test task',
        )
        a = list(m.activities.values())[0]
        assert_equal('test task', a.title)
        assert_false(a.project)

    def test_new_project(self):
        m = Manager()
        m.new_activity(
            title='test project',
            project=True
        )
        a = list(m.activities.values())[0]
        assert_equal('test project', a.title)
        assert_true(a.project)

    def test_modify_task_to_project(self):
        m = Manager()
        m.new_activity(
            title='test activity',
        )
        a = list(m.activities.values())[0]
        assert_false(a.project)
        m.list_activities()  # put activity in context
        m.modify_activity('0', project=True)
        assert_true(a.project)
