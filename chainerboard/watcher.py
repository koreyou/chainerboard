# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import contextlib
import logging
import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


logger = logging.getLogger(__name__)


class LogHandler(FileSystemEventHandler):
    def __init__(self, inputfile, timeline_handler):
        self._watch_path = inputfile
        self._timeline_handler = timeline_handler
        super(LogHandler, self).__init__()

    def _on_change(self, target_path):
        target_path = os.path.realpath(target_path)
        watch_path = os.path.realpath(self._watch_path)
        if target_path == watch_path:
            logger.info("modification detected! Updating %s" % target_path)
            self._timeline_handler.load(target_path)

    def on_modified(self, event):
        self._on_change(event.src_path)

    def on_created(self, event):
        self._on_change(event.src_path)

    def on_deleted(self, event):
        self._on_change(event.src_path)

    def on_moved(self, event):
        self._on_change(event.dest_path)


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
