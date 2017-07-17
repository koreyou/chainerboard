# -*- coding: utf-8 -*-
"""
Deals with time-dependent data
"""
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import logging
from collections import OrderedDict

from chainerboard.exceptions import KeyDisappearedException
from chainerboard import util

logger = logging.getLogger(__name__)


class KeyValuePair(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value


class TimelineBase(object):
    def __init__(self):
        self._uninitialized = True
        self._update_state_hash()

    def _update_state_hash(self):
        self._state_hash = util.random_hash(12)

    def _initialize_times(self, epoch, iteration, time_elapsed):
        self._epoch = None if epoch is None else []
        self._iteration = None if iteration is None else []
        self._elapsed_time = None if time_elapsed is None else []
        self._uninitialized = False

    def _append_time(self, epoch, iteration, elapsed_time):
        if self._epoch is not None:
            self._epoch.append(epoch)

        if self._iteration is not None:
            self._iteration.append(iteration)

        if self._elapsed_time is not None:
            self._elapsed_time.append(elapsed_time)

    def _extract_value_impl(self, dic, epoch, iteration, elapsed_time):
        """
        Implementation for extracting of values.
        This function should return ``True`` if there were any updates otherwise
        ``False``.
        """
        raise NotImplementedError()

    def extract_value(self, dic, epoch, iteration, elapsed_time):
        if self._uninitialized:
            self._initialize_times(epoch, iteration, elapsed_time)

        ret = self._extract_value_impl(dic, epoch, iteration, elapsed_time)
        assert isinstance(ret, bool)
        if ret:
            self._update_state_hash()
        return ret

    @property
    def elapsed_time(self):
        return self._elapsed_time

    @property
    def epoch(self):
        return self._epoch

    @property
    def iteration(self):
        return self._iteration

    @property
    def state_hash(self):
        return self._state_hash


class Timeline(TimelineBase):
    def __init__(self, key):
        super(Timeline, self).__init__()
        self._key = key
        self._key_std = key + '.std'
        self._value = []

    def _extract_value_impl(self, dic, epoch, iteration, elapsed_time):
        updated = False
        if self._key_std in dic:
            std = dic.pop(self._key_std)
            updated = True
        if self._key in dic:
            val = dic.pop(self._key)
            self._value.append(val)
            self._append_time(epoch, iteration, elapsed_time)
            updated = True
        return updated

    @property
    def value(self):
        return self._value


class MicroAverageTimeline(TimelineBase):
    def __init__(self, total_key, correct_key):
        super(MicroAverageTimeline, self).__init__()
        self._total_key = total_key
        self._correct_key = correct_key
        self._value = []

    def _extract_value_impl(self, dic, epoch, iteration, elapsed_time):
        updated = False
        if self._correct_key in dic:
            # Assume that both keys are in dic
            correct = dic.pop(self._correct_key)
            try:
                total = dic.pop(self._total_key)
            except KeyError:
                raise KeyDisappearedException(self._total_key)
            micro_average = correct / float(total)
            self._value.append(micro_average)
            self._append_time(epoch, iteration, elapsed_time)
            updated = False
        elif self._total_key in dic:
            # Only total_key exists in dic -> raise Error
            raise KeyDisappearedException(self._correct_key)
        return updated

    @property
    def value(self):
        return self._value


class TensorTimeline(TimelineBase):
    """
    Timeline for visualizing tensors. This is intended for logs from
    [chainer.extensions.ParameterStatistics](https://docs.chainer.org/en/latest/reference/generated/chainer.training.extensions.ParameterStatistics.html)

    .. warning:: Class constructor has side effect to ``data_keys`` and
                 ``grad_keys``

    Args:
        data_keys (dict): Mapping from metric name (str) to key string (str).
        grad_keys (dict): Mapping from metric name (str) to key string (str).

    """

    _DEFAULT_PERCENTILE_KEYS = {
        'percentile/0': r'0.13%',
        'percentile/1': r'2.28%',
        'percentile/2': r'15.87%',
        'percentile/3': r'50%',
        'percentile/4': r'84.13%',
        'percentile/5': r'97.72%',
        'percentile/6': r'99.87%',
    }
    def __init__(self, data_keys, grad_keys):
        super(TensorTimeline, self).__init__()
        self._data_percentiles_keys = {
            k: data_keys.pop(k) for k in data_keys.keys() if k.startswith('percentile/')}
        try:
            self._data_percentiles_names = {
                k: self._DEFAULT_PERCENTILE_KEYS[k]
                for k in self._data_percentiles_keys.keys()
            }
        except KeyError:
            self._data_percentiles_names = {
                k: k for k in self._data_percentiles_keys.keys()
            }
        self._data_percentiles = OrderedDict(
            ((k, []) for k in sorted(self._data_percentiles_keys.keys()))
        )
        self._data = {k: [] for k in data_keys.keys()}
        self._data_keys = data_keys

        self._grad_percentiles_keys = {
            k: grad_keys.pop(k) for k in grad_keys.keys() if k.startswith('percentile/')}
        self._grad_percentiles = OrderedDict(
            ((k, []) for k in sorted(self._grad_percentiles_keys.keys()))
        )
        self._grad = {k: [] for k in grad_keys.keys()}
        self._grad_keys = grad_keys

    def _extract_value_impl(self, dic, epoch, iteration, elapsed_time):
        if next(self._data_percentiles_keys.itervalues()) not in dic:
            # Assume tensor is absent in dic
            return False
        self._append_time(epoch, iteration, elapsed_time)
        try:
            for k, dic_key in self._data_percentiles_keys.iteritems():
                self._data_percentiles[k].append(dic.pop(dic_key))
            for k, dic_key in self._data_keys.iteritems():
                self._data[k].append(dic.pop(dic_key))
            for k, dic_key in self._grad_percentiles_keys.iteritems():
                self._grad_percentiles[k].append(dic.pop(dic_key))
            for k, dic_key in self._grad_keys.iteritems():
                self._grad[k].append(dic.pop(dic_key))
        except KeyError:
            raise KeyDisappearedException(dic_key)
        return True

    def get_percentiles(self):
        percentiles = [
            {'label': self._data_percentiles_names[k], 'data': v}
            for k, v in self._data_percentiles.iteritems()
        ]
        if 'min' in self._data and 'max' in self._data:
            percentiles = (
                [{'label': 'min', 'data': self._data['min']}, ] +
                percentiles +
                [{'label': 'max', 'data': self._data['max']}, ]
            )
        return percentiles
