# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals

__all__ = ["app", "timeline_handler"]

from flask import Flask

import chainerboard as _chainerboard


app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

# FIXME: enable debug mode in beta
app.debug = True

timeline_handler = _chainerboard.TimelineHandler()

# imports on bottom to avoid import loops
import chainerboard.app.root
import chainerboard.app.events
import chainerboard.app.histograms
