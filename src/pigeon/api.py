# -*- coding: utf-8 -*-
from calendar import timegm
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from queue import Queue, Full, Empty
import socket
from time import time

from pytz import UTC

from .response_wrapper import IterableWrapper


_CALLS_BUFFER_LIMIT = 1000

_SEND_LIMIT = 5


class Pigeon(object):
    """ Send call reports to Riemann. """

    def __init__(self, *args, **kwds):
        self._get_riemann_client = kwds.pop("get_riemann_client")
        self._events_host = kwds.pop("host", socket.gethostname())
        self._call_events = Queue(1000)
        self._event_workers = ThreadPoolExecutor(max_workers=1)
        super().__init__(*args, **kwds)

    def _process_call_metrics(self):
        with self._get_riemann_client() as client:
            try:
                event = self._call_events.get(False)
            except Empty:
                event = None
            while event:
                try:
                    client.event(**event)
                except Exception:
                    pass  # drop event, no connection
                try:
                    event = self._call_events.get(False)
                except Empty:
                    event = None
            try:
                client.flush()
            except Exception:
                pass  # ignore, events lost

    def _monitor_end_call(self, env, start, url, status):
        end = time()
        event = {
            "time": timegm(datetime.utcnow().replace(tzinfo=UTC).timetuple()),
            "host": self._events_host,
            "service": url,
            "state": status,
            "metric_sint64": int(round((end - start) * 1000)),
            "tags": ["total"]
        }
        try:
            self._call_events.put_nowait(event)
        except Full:
            pass  # silently drop event
        else:
            if self._call_events.qsize() > _SEND_LIMIT:
                self._event_workers.submit(self._process_call_metrics)

    def __call__(self, env, start_response):
        status_recorder = ["000"]

        def _start_response(status, headers, status_recorder=status_recorder):
            start_response(status, headers)
            status_recorder[0] = status

        def call_back(env, start, url, status_recorder=status_recorder):
            self._monitor_end_call(env, start, url, status_recorder[0][:3])

        return IterableWrapper(
            call_back, env, time(), super().__call__(env, _start_response))
