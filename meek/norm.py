#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text normalization
"""

from textnorm import normalize_space, normalize_unicode


def norm(s: str) -> str:
    return normalize_space(normalize_unicode(s))
