# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import contextlib
import logging
import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogHandler(FileSystemEventHandler):
    def __init__(self, inputfile, timeline_handler):
        self._watch_path = inputfile
        self._timeline_handler = timeline_handler
        super(LogHandler, self).__init__()

    def on_modified(self, event):
        # FIXME: this is probanly plaform dependent; better way of comparing?
        if os.path.samefile(event.src_path, self._watch_path):
            logger.info("modification detected! Updating %s" % event.src_path)
            self._timeline_handler.load(event.src_path)


@contextlib.contextmanager
def watch_file(inputfile, timeline_handler):
    # log handler does not load on detecting the initial file
    timeline_handler.load(inputfile)
    event_handler = LogHandler(inputfile, timeline_handler)
    observer = Observer()
    observer.schedule(event_handler,
                      os.path.dirname(os.path.abspath(inputfile)))
    observer.start()
    yield
    observer.stop()
    observer.join()
