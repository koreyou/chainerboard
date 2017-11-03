# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import logging

from flask import render_template, redirect, url_for

from chainerboard.app import app


logger = logging.getLogger(__name__)


@app.route('/')
def index():
    return redirect(url_for('events'))


@app.route('/events')
def events():
    return render_template('layouts/events.html')


@app.route('/histograms')
def histograms():
    return render_template('layouts/histograms.html')
