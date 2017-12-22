# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import logging

import click

import chainerboard
from chainerboard.app import app, timeline_handler
from chainerboard.watcher import watch_file

logging.basicConfig(level=logging.INFO)
logging.getLogger('werkzeug').setLevel(logging.WARN)

logger = logging.getLogger(__name__)


@click.command('chainerboard')
@click.argument('inputfile', type=click.Path(exists=True))
@click.option('-p', '--port', type=int, default=6006, help="Port number to use")
@click.version_option(chainerboard.__version__, prog_name='chainerboard')
def cli(inputfile, port):
    """
    An unofficial visualization tool for chainer, inspired by tensorboard
    chainerboard allows visualization of log from chainer.extensions.LogReport.
    """
    with watch_file(inputfile, timeline_handler):
        # use_reloader=False because it makes watchdog unstoppable
        logger.info('Running on http://localhost:%d' % port)
        app.run(host='0.0.0.0', port=port, use_reloader=False)
