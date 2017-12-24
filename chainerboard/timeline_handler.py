# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import hashlib
import json
import logging
import re
import threading

import six

from chainerboard import util
from chainerboard.exceptions import KeyDisappearedException, ParseError
from chainerboard.timeline import Timeline, TensorTimeline, MicroAverageTimeline

logger = logging.getLogger(__name__)


def _find_partial_match(dic, key):
    ret = []
    for k in six.iterkeys(dic):
        if key in k:
            ret.append(k)
    return ret


def _find_get_patten_match_single(dic, match_func):
    """
    Find a matching key from dict. This function returns value when the
    found match is the only match in the dict.

    Args:
        dic (dict): Mapping from a key (str) to corresponding metric (numeric)
            from one output of LogReporter.
        match_func (func): A function that takes a variable (str) as input and
            returns a bool if it is a valid match.

    Returns:
        str or None

    """
    # match_func(str) -> bool
    found_key = None
    for k in six.iterkeys(dic):
        if match_func(k):
            if found_key is None:
                found_key = k
            else:
                # The second match is found
                return None
    return found_key


def _find_partial_match_single(dic, key):
    return _find_get_patten_match_single(dic, lambda k, key=key: key in k)


def _find_regex_match_single(dic, pat):
    pat = re.compile(pat)
    return _find_get_patten_match_single(
        dic, lambda k, pat=pat: pat.search(k) is not None)


def _try_find_fallback(dic, key, warn=True):
    """
    Try to find a key in dic. It will try to find a exact match first. If it
    fails, it will fall back to find a partial match.

    Args:
        dic (dict): Mapping from a key (str) to corresponding metric (numeric)
            from one output of LogReporter.
        key (str): Key to find

    Returns:
        str or None

    """
    if key in dic:
        return key

    partial_matches = _find_partial_match(dic, key)
    if warn and len(partial_matches) > 1:
        logger.warn("Multiple match for key %s: %s" % (key, str(partial_matches)))
    return partial_matches[0] if len(partial_matches) > 0 else None


def _try_find_conservative(dic, key):
    """
    Try to find a key in dic. These keys are less important, so extract only if
    confident.

    These are currently dedicated to ``loss`` and ``accuracy``

    .. warning:: This function have side effects to dic

    Args:
        dic (dict): Mapping from a key (str) to corresponding metric (numeric)
            from one output of LogReporter.
        key (str): Key to find

    Returns:
        str or None: The key value
    """
    # These keys are less important, so extract only if confident
    key_default = 'main/%s' % key
    if key_default in dic:
        return key_default
    found = _find_regex_match_single(dic, r'%s$' % re.escape(key))

    return found


def match_data_grad(dic):
    """
    Search data and grad properties, which are created by ParameterStatistics.

    Args:
        dic (dict): Mapping from a key (str) to corresponding metric (numeric)
            from one output of LogReporter.

    Returns:
        dict: ret[obj_name][`data` or `grad`][metric_name] -> key
            e.g.
            ::

                {'main/link/layer/W': {
                  'data': {
                    'percentile/1': 'main/link/layer/W/data/percentile/1',
                    'zeros': 'main/link/layer/W/data/zeros',
                    ...
                    },
                  'grad': {
                    'percentile/1': 'main/link/layer/W/grad/percentile/1',
                    ...
                    }
                  },
                  ...
                }

    """
    matched = {}
    for k in six.iterkeys(dic):
        if k.endswith('.std'):
            continue
        idx = k.find('/data/')
        if idx >= 0:
            obj_name = k[:idx]
            if obj_name not in matched:
                matched[obj_name] = {'data': {}}
            elif 'data' not in matched[obj_name]:
                matched[obj_name]['data'] = {}
            matched[obj_name]['data'][k[idx + 6:]] = k
            continue
        idx = k.find('/grad/')
        if idx < 0:
            # Not found, so continue the for loop
            continue
        obj_name = k[:idx]
        if obj_name not in matched:
            matched[obj_name] = {'grad': {}}
        elif 'grad' not in matched[obj_name]:
            matched[obj_name]['grad'] = {}
        matched[obj_name]['grad'][k[idx + 6:]] = k

    return matched


def _hash_json(dic):
    """
    Hash json parsable object.

    Args:
        dic (list of dict): Json parsable object.

    Returns:
        bytes: 32 characters hash

    """
    json_dump = json.dumps(dic, sort_keys=True).encode('utf-8')
    return hashlib.md5(json_dump).hexdigest()


def _lock(f):
    """ decorator which locks class method
    You need property _lock defined as in the following.
    self._lock = threading.Lock()
    """
    def body(self, *args, **kwargs):
        with self._lock:
            return f(self, *args, **kwargs)
    return body


class TimelineHandler(object):
    """
    This class aggregates Timelines to handle a series of training metrics.

    TimelineHandler is controlled with ``session_id`` if read data
    contradict with previously read data, it will assign new
    ``session_id``
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._clear()

    def _clear(self):
        self.tensors = {}
        self._events = {}
        self._time_uninitialized = True
        self._done_idx = 0
        self._digest = None
        self._session_id = util.random_hash(12)

    @property
    def session_id(self):
        return self._session_id

    def _initialize_time_keys(self, dic):
        self._epoch_key = _try_find_fallback(dic, 'epoch')
        self._iteration_key = _try_find_fallback(dic, 'iteration')
        self._elapsed_time_key = _try_find_fallback(dic, 'elapsed_time')
        if (self._epoch_key is None and self._iteration_key is None
                and self._elapsed_time_key is None):
            raise ParseError(
                'None of epoch, iteration and elapsed_time was found in json file.')
        self._time_uninitialized = False

    def _extract_time(self, dic):
        epoch = dic.pop(self._epoch_key, None)
        iteration = dic.pop(self._iteration_key, None)
        elapsed_time = dic.pop(self._elapsed_time_key, None)
        # Do sanity check first. Abort if something is wrong.
        if self._epoch_key is not None and epoch is None:
            raise KeyDisappearedException(self._epoch_key)
        if self._iteration_key is not None and iteration is None:
            raise KeyDisappearedException(self._iteration_key)
        if self._elapsed_time_key is not None and elapsed_time is None:
            raise KeyDisappearedException(self._elapsed_time_key)
        return epoch, iteration, elapsed_time

    def _identify_predefined_metrics(self, dic, epoch, iteration, elapsed_time):
        """
        Key name for the important metrics can change by the training configuration.
        This function determines the key names of such variables and groups
        them according its guess.

        Args:
            dic:
        """
        events = {}
        loss_key = _try_find_conservative(dic, 'loss')
        if loss_key is not None:
            events[loss_key] = Timeline(loss_key)
        accuracy_key = _try_find_conservative(dic, 'accuracy')
        if accuracy_key is not None:
            events[accuracy_key] = Timeline(accuracy_key)
        # From chainer.extensions.MicroAverage
        # These were not written in the code but is written in example
        total_key = 'main/total'
        correct_key = 'main/correct'
        if total_key in dic and correct_key in dic:
            events[correct_key] = MicroAverageTimeline(total_key, correct_key)

        for k in six.iterkeys(events):
            events[k].extract_value(dic, epoch, iteration, elapsed_time)
        self._events.update(events)

    def _identify_tensors(self, dic, epoch, iteration, elapsed_time):
        # For now just throw them away
        matched = match_data_grad(dic)
        tensors = {}
        for name, key_info in six.iteritems(matched):
            data = key_info['data']
            grad = key_info['grad']
            tensors[name] = TensorTimeline(data, grad)

        for k in six.iterkeys(tensors):
            tensors[k].extract_value(dic, epoch, iteration, elapsed_time)
        self.tensors.update(tensors)

    def _identify_misc(self, dic, epoch, iteration, elapsed_time):
        # For now just throw them away
        events = {}
        for k in six.iterkeys(dic):
            if k.endswith('.std'):
                continue
            events[k] = Timeline(k)
        for k in six.iterkeys(events):
            events[k].extract_value(dic, epoch, iteration, elapsed_time)
        self._events.update(events)

    def _extract(self, dic):
        if self._time_uninitialized:
            self._initialize_time_keys(dic)
        epoch, iteration, elapsed_time = self._extract_time(dic)
        for k in six.iterkeys(self._events):
            self._events[k].extract_value(dic, epoch, iteration, elapsed_time)
        for k in six.iterkeys(self.tensors):
            self.tensors[k].extract_value(dic, epoch, iteration, elapsed_time)
        self._identify_predefined_metrics(dic, epoch, iteration, elapsed_time)
        self._identify_tensors(dic, epoch, iteration, elapsed_time)
        self._identify_misc(dic, epoch, iteration, elapsed_time)
        if len(dic) > 0:
            logger.debug("Ignored keys: %s" % ', '.join(map(str, six.iterkeys(dic))))

    @_lock
    def update(self, logs):
        """
        Update the handler from log dictionaries.
        This function is idempotent.

        ..warning :: I have not tested much that it is actually idempotent.

        Args:
            logs (list of dict): Parsed log file, each dict representing a
                report from the single output of Reporter.

        """
        digest = _hash_json(logs[:self._done_idx])
        if self._digest != digest:
            old_session = self._session_id
            self._clear()
            logger.debug(
                "Digest unmatch; setting new session (%s -> %s)" %
                (old_session, self._session_id)
            )

        if self._done_idx < len(logs):
            self._digest = _hash_json(logs)
            while self._done_idx < len(logs):
                self._extract(logs[self._done_idx])
                self._done_idx += 1
            logger.debug('Parsed up to line:%d' % (self._done_idx))

    def get_events_ids(self):
        return list(six.iterkeys(self._events))

    def get_tensors_ids(self):
        return list(six.iterkeys(self.tensors))

    @property
    def events(self):
        return self._events

    @property
    def lock(self):
        return self._lock

    def load(self, path):
        """
        Aggregate records and crete timeline data that is suitable for drawing
        plots.
        """
        with open(path) as fin:
            data = json.load(fin)
        self.update(data)
