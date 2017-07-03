# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import logging
import os

import click
from flask import Flask, render_template, redirect, url_for, jsonify, request

import chainerboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


script_dir = os.path.dirname(__file__)

app = Flask(
    __name__,
    template_folder=os.path.join('..', 'templates'),
    static_folder=os.path.join('..', 'static')
)
app.debug = True

logpath = None
timeline = None


def load_data():
    """
    Aggregate records and crete timeline data that is suitable for drawing
    plots.

    Returns:
        dict: Key is the label of data. Each value is a ``dict`` with an
            element ``"globalstep"`` (list of int) and the ``"values"``
            (list of float)
    """
    global logpath, timeline
    with open(logpath) as fin:
        data = json.load(fin)
    timeline.update(data)
    logger.info('loaded json')


@app.route('/')
def index():
    return redirect(url_for('events'))


@app.route('/events')
def events():
    return render_template('layouts/events.html')


@app.route('/events/plots', methods=['GET'])
def get_events_plots():
    ids = timeline.get_events_ids()
    return jsonify(ids)


@app.route('/events/data', methods=['GET'])
def get_events_data():
    g = request.args.get('graphId')
    logger.info(g)

    data = {
        'x': timeline.events[g].iteration,
        'y': timeline.events[g].value
    }

    return jsonify(data)


@click.command()
@click.argument('inputfile', type=click.Path(exists=True))
@click.option('-p', '--port', type=int, default=6006)
def cli(inputfile, port):
    global logpath, timeline
    logpath = inputfile
    timeline = chainerboard.TimelineHandler()
    load_data()
    app.run(host='0.0.0.0', port=port)
