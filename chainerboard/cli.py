# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import logging
import os
import re

import click
import colorlover as cl
import numpy as np
import plotly
from flask import Flask, render_template, redirect, url_for, Response, jsonify, \
    request

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

logdir = None
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
    global logdir
    reporter = chainerboard.Reporter.load(logdir)
    logger.info('loaded json')
    return reporter.to_timeline()


def moving_average(x, y, window):
    weights = np.repeat(1.0, window) / window
    ma = np.convolve(y, weights, 'valid')
    x = x[window // 2:len(y) - (window // 2)]
    return x, ma


@app.route('/')
def index():
    return redirect(url_for('events'))


@app.route('/events')
def events():
    return render_template('layouts/events.html')


@app.route('/events/plots', methods=['GET'])
def get_events_plots():
    ids = timeline.keys()
    return jsonify(ids)


@app.route('/events/data', methods=['GET'])
def get_events_data():
    g = request.args.get('graphId')
    logger.info(g)
    group = timeline[g]
    colorpalette = cl.to_numeric(cl.scales['7']['qual']['Set1'])

    data = []
    for (l, d), color in zip(group.iteritems(), colorpalette):
        color = '#{:02X}{:02X}{:02X}'.format(*map(int, color))
        data.append(dict(
            x=d[0],
            y=d[1],
            type='scatter',
            marker={'color': color},
            name=l,
            opacity=0.3,
        ))
        if len(d[0]) > 11:
            x, y = moving_average(d[0], d[1], 11)
            data.append(dict(
                x=x,
                y=y,
                type='scatter',
                name=l + '(window=11)',
                marker={'color': color},
                opacity=0.9
            ))

    graph = dict(
         data=data,
         layout=dict(
            title=g,
            xaxis={'title': 'steps'},
            yaxis={'type': 'log'}
         )
    )

    graph_json = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)

    logger.info('created graph json')
    # do not use jsonify because we want to use custom encoder
    return Response(graph_json, mimetype='application/json')


@click.command()
@click.argument('inputfile', type=click.Path(exists=True))
@click.option('-p', '--port', type=int, default=6006)
def cli(inputfile, port):
    global logdir, timeline
    logdir = inputfile
    timeline = load_data()
    app.run(host='0.0.0.0', port=port)
