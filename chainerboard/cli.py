# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import logging
import os

import click
from flask import Flask, render_template, redirect, url_for, jsonify, request
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

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
timeline = None


def init_timeline():
    global timeline
    timeline = chainerboard.TimelineHandler()


def load_data(path):
    """
    Aggregate records and crete timeline data that is suitable for drawing
    plots.

    Returns:
        dict: Key is the label of data. Each value is a ``dict`` with an
            element ``"globalstep"`` (list of int) and the ``"values"``
            (list of float)
    """
    global timeline
    with open(path) as fin:
        data = json.load(fin)
    timeline.update(data)
    logger.info('loaded json')


class LogHandler(FileSystemEventHandler):
    def __init__(self, inputfile):
        self._watch_path = inputfile
        super(LogHandler, self).__init__()

    def on_modified(self, event):
        # FIXME: this is probanly plaform dependent; better way of comparing?
        if os.path.samefile(event.src_path, self._watch_path):
            logger.info("modification detected! Updating %s" % event.src_path)
            load_data(event.src_path)

    def on_deleted(self, event):
        if event.src_path == self._watch_path:
            init_timeline()


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


@app.route('/events/updated', methods=['GET'])
def get_events_updated():
    g = request.args.get('graphId')
    logger.info(g)

    # Placeholder for now
    return jsonify({"update": False})


@click.command()
@click.argument('inputfile', type=click.Path(exists=True))
@click.option('-p', '--port', type=int, default=6006)
def cli(inputfile, port):
    init_timeline()
    load_data(inputfile)

    event_handler = LogHandler(inputfile)
    observer = Observer()
    observer.schedule(event_handler,
                      os.path.dirname(os.path.abspath(inputfile)))
    observer.start()
    # use_reloader=False because it makes watchdog unstoppable
    app.run(host='0.0.0.0', port=port, use_reloader=False)

    observer.stop()
    observer.join()
