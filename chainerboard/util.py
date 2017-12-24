# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import random
import string

import six

_LETTERS = six.u(string.ascii_letters + string.digits)


def random_hash(n, seed=None):
    random.seed(seed)
    return ''.join((random.choice(_LETTERS) for _ in six.moves.xrange(n)))
