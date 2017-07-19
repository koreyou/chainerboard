# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import logging
from collections import defaultdict
import warnings

from flask import jsonify, request
import numpy as np

from chainerboard import util
from chainerboard.app import app, timeline_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _cleanse_plots(x, y):
    """
    Replace NaN, inf or large number that cause harm to 'nan' (str)

    Accoding to ecma-262, largest possible value is 1.7976931348623157e308.
    Let's make anything above 1.0e308 infinity.

    Plotly can properly handle 'nan'.

    Args:
        x (list): index value of the timeline. We do not check for
            invalid value within x.
        y (list of float): Metric value to visualive.

    Returns:
        list: cleaned y

    """
    _FLOAT_CUTOFF_MAX = np.float(1.7976931348623157e308)
    _FLOAT_CUTOFF_MIN = np.float(-1.7976931348623159e308)
    x = np.asarray(x)
    y = np.asarray(y)
    assert len(x) == len(y)
    mask = np.isfinite(y)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        if np.isfinite(_FLOAT_CUTOFF_MAX):
            mask = np.logical_and(mask, y <= _FLOAT_CUTOFF_MAX)
        if np.isfinite(_FLOAT_CUTOFF_MIN):
            mask = np.logical_and(mask, y >= _FLOAT_CUTOFF_MIN)
    return [y[i] if mask[i] else 'nan' for i in xrange(len(y))]


@app.route('/events/data', methods=['GET'])
def get_events_data():
    g = request.args.get('graphId')
    logger.info(g)

    x, y = _cleanse_plots(timeline_handler.events[g].iteration,
                       timeline_handler.events[g].value)
    data = {
        'x': x,
        'y': y,
        'stateHash': timeline_handler.events[g].state_hash
    }

    return jsonify(data)


def _recursive_find_parent(graph, graph_to_group):
    if graph.id in graph_to_group:
        return graph_to_group[graph.id]
    else:
        if graph.parent is None:
            return None
        else:
            return _recursive_find_parent(graph.parent, graph_to_group)


@app.route('/events/updates', methods=['POST'])
def get_events_updates():
    u"""
    Given current state, return updates.
    The `Parameters` show the content of payload, and `Returns` show the content
    of return body.

    We randomly associate groupId of 12 alphabetical + numeric characters.
    12 chars means that it needs approx 2.5e9 groups to get 0.1% chance for
    group ids to collide.

    Parameters
        active (dict): Current active graphs' states as a group id-graph ids
            pairs ``{"0d9asjan2ija": [id1, id2, ..], ... }``
        states (dict): Mapping from graph id to state hash
        sessionId (str): Session ID that was originally given by this API.
            Should give empty string if no session ID is associated.

    Returns:
        updateType (str): 'new' or 'update'
        sessionId (str): Session ID of 12 ascii characters
        newPlots (list of dict): Newly detected plots. ``"type"`` field (str)
            tells client of action to take; ``"new"`` if the new graph does not
            belong to any group, ``"hidden"`` if it should not be shown and
            ``"append"`` if it should appended to existing group.
            ``"groupId"`` field (str) show group id to add the graph.
            ``"graphId"`` is the graph id that client can use to get the data
            for the graph.
        updates (dict): Notifies graphs to update. Maps group id (str)
            to IDs of graphs to update (list of str).
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
    graph_to_group = {g: group for group, graphs in active.iteritems()
                      for g in graphs}

    # First determine graphs to add/update
    new_plots = []
    for g in timeline_handler.get_events_ids():
        if g not in states:
            # Currently does not implent type=append or hidden
            group_id = util.random_hash(12)
            new_plots.append({
                'type': 'new',
                'groupId': group_id,  # create new group id
                'name': g,
                'graphId': g
            })
            active[group_id] = [g]

    updates = defaultdict(list)
    for group_id, graphs in active.iteritems():
        for g in graphs:
            if timeline_handler.events[g].state_hash != states.get(g, ''):
                updates[group_id].append(g)

    return jsonify({
        'updateType': update_type,
        'sessionId': session_id,
        'newPlots': new_plots,
        'updates': dict(updates)
    })
