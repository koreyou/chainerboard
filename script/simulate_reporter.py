# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import json
import logging
import time

import click


@click.command()
@click.argument('infile', type=click.Path(exists=True))
@click.argument('outfile', type=click.Path())
@click.option('-t', '--time-interval', type=float, default=10.,
              show_default=True)
@click.option('-q', '--quiet', is_flag=True, show_default=True)
def run(infile, outfile, time_interval, quiet):
    logging.basicConfig(level=logging.WARN if quiet else logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('loading input file %s ...' % infile)
    with open(infile) as fin:
        # Do not use click.File because we want close the file asap
        data = json.load(fin)
    n = len(data)
    logger.info(
        'loading input file %s done. %d data found.'% (infile, n))
    for i in xrange(len(data)):
        logger.info('Sleeping for %d sec [%d/%d] ...' % (time_interval, i+1, n))
        time.sleep(time_interval)
        with open(outfile, 'w') as fout:
            json.dump(data[:(i+1)], fout)
        logger.info('Dumped %dth/%d data to %s' % (i+1, n, outfile))


if __name__ == '__main__':
    # This script is not installed with cli.py because it is part of debugging
    # code
    run()