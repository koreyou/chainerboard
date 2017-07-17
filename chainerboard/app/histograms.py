# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import logging

from flask import jsonify, request

from chainerboard.app import app, timeline_handler
from chainerboard import util

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/histograms/data', methods=['GET'])
def get_histograms_data():
    g = request.args.get('graphId')

    data = {
        'x': timeline_handler.tensors[g].iteration,
        'y': timeline_handler.tensors[g].get_percentiles(),
        'stateHash': timeline_handler.tensors[g].state_hash
    }

    return jsonify(data)


@app.route('/histograms/updates', methods=['POST'])
def get_histograms_updates():
    u"""
    Given current state, return updates.
    The `Parameters` show the content of payload, and `Returns` show the content
    of return body.

    We randomly associate groupId of 12 alphabetical + numeric characters.
    12 chars means that it needs approx 2.5e9 groups to get 0.1% chance for
    group ids to collide.

    Parameters
        active (dict): Current active graphs' states as a group id-graph ids
            pairs ``{"0d9asjan2ija": id1, ... }``
        states (dict): Mapping from graph id to state hash
        sessionId (str): Session ID that was originally given by this API.
            Should give empty string if no session ID is associated.

    Returns:
        updateType (str): 'new' or 'update'
        sessionId (str): Session ID of 12 ascii characters
        newPlots (list of dict): Newly detected plots. ``"type"`` field (str)
            tells client of action to take; ``"new"`` if the new graph does not
            belong to any group and ``"hidden"`` if it should not be shown.
            ``"graphId"`` is the graph id that client can use to get the data
            for the graph.
        updates (list of str): IDs of graphs to update (list of str).
            The list does includes graphs in newPlots.

    """
    session_id = request.json['sessionId']
    if session_id  == '':
        # no session id associated
        session_id = util.random_hash(12)
        logger.info("creating new session %s" % session_id)
        states = {}
        active = {}
        update_type = "new"
    else:
        assert isinstance(session_id, (bytes, unicode)) and len(session_id) == 12
        states = request.json['states']
        active = request.json['active']
        update_type = "update"

    # First determine graphs to add/update
    new_plots = []
    for g in timeline_handler.get_tensors_ids():
        if g not in states:
            # Currently does not implent type=append or hidden
            graph_div = util.random_hash(12)
            new_plots.append({
                'type': 'new',
                'graphDiv': graph_div,
                'graphId': g
            })
            active[graph_div] = g

    updates = []
    for group_id, g in active.iteritems():
        if timeline_handler.tensors[g].state_hash != states.get(g, ''):
            updates.append(group_id)

    return jsonify({
        'updateType': update_type,
        'sessionId': session_id,
        'newPlots': new_plots,
        'updates': updates
    })
