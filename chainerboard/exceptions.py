# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals


class KeyDisappearedException(Exception):
    def __init__(self, key):
        message = "Key '%s' has disappeared from data." % key
        super(KeyDisappearedException, self).__init__(message)


def warn_key_disappered(logger, key):
    logger.warn("Key '%s' has disappeared from data." % key)


class ParseError(Exception):
    pass

