# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import logging

from flask import jsonify, request

from chainerboard.app import app, timeline_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/histograms/plots', methods=['GET'])
def get_histograms_plots():
    ids = timeline_handler.get_tensors_ids()
    return jsonify(ids)


@app.route('/histograms/data', methods=['GET'])
def get_histograms_data():
    g = request.args.get('graphId')
    logger.info(g)

    data = {
        'x': timeline_handler.tensors[g].iteration,
        'y': [{'label': k, 'data': v} for k, v in
              timeline_handler.tensors[g].percentiles.iteritems()]
    }

    return jsonify(data)


@app.route('/histograms/updated', methods=['GET'])
def get_histograms_updated():
    g = request.args.get('graphId')
    logger.info(g)

    # Placeholder for now
    return jsonify({"update": False})
