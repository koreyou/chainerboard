# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals


from chainerboard.app import events


def test_clease_plots():
    y_input = [0.1125, -0.1, float('inf'), 2.091]
    x_input = [0, 1, 2, 3]
    y = events._cleanse_plots(x_input, y_input)
    assert [0.1125, -0.1, 'nan', 2.091] == y

    # it should accept empty list
    y = events._cleanse_plots([], [])
    assert [] == y

    y_input = [float('inf')]
    x_input = [0]
    y = events._cleanse_plots(x_input, y_input)
    assert ['nan'] == y

    y_input = [0.1125, -0.1, float('nan'), 2.091]
    x_input = [0, 1, 2, 3]
    y = events._cleanse_plots(x_input, y_input)
    assert [0.1125, -0.1, 'nan', 2.091] == y

    # should not change (slightly) large value
    y_input = [1.2e5, -0.1]
    x_input = [0, 1]
    y = events._cleanse_plots(x_input, y_input)
    assert [1.2e5, -0.1] == y

    # should replace really large value
    y_input = [1.0e309, -0.1]
    x_input = [0, 1]
    y = events._cleanse_plots(x_input, y_input)
    assert ['nan', -0.1] == y
