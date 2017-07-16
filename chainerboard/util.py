# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import random
import string


_LETTERS = string.letters + string.digits


def random_hash(n, seed=None):
    random.seed(seed)
    return ''.join((random.choice(_LETTERS) for _ in xrange(n)))
