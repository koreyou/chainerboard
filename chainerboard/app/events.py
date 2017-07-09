# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import logging

from flask import jsonify, request

from chainerboard.app import app, timeline_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/events/plots', methods=['GET'])
def get_events_plots():
    ids = timeline_handler.get_events_ids()
    return jsonify(ids)


@app.route('/events/data', methods=['GET'])
def get_events_data():
    g = request.args.get('graphId')
    logger.info(g)

    data = {
        'x': timeline_handler.events[g].iteration,
        'y': timeline_handler.events[g].value
    }

    return jsonify(data)


@app.route('/events/updated', methods=['GET'])
def get_events_updated():
    g = request.args.get('graphId')
    logger.info(g)

    # Placeholder for now
    return jsonify({"update": False})
