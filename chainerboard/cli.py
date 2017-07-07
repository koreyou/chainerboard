# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import logging

import click

from chainerboard.app import app, timeline_handler
from chainerboard.watcher import watch_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.argument('inputfile', type=click.Path(exists=True))
@click.option('-p', '--port', type=int, default=6006)
def cli(inputfile, port):

    with watch_file(inputfile, timeline_handler):
        # use_reloader=False because it makes watchdog unstoppable
        app.run(host='0.0.0.0', port=port, use_reloader=False)
