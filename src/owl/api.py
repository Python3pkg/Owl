# -*- coding: utf-8 -*-
from calendar import timegm
from datetime import datetime, timedelta
from queue import Queue, Full
from socket import gethostname
from threading import Thread
from time import time

from pytz import UTC

from .response_wrapper import IterableWrapper


_CALLS_BUFFER_LIMIT = 1000

_SEND_LIMIT = 5

_MAX_SEND_INTERVALL = timedelta(seconds=5)


class Owl(object):
    """ Send call reports to Riemann. """

    def __init__(self, *args, **kwds):
        self._get_riemann_client = kwds.pop("get_riemann_client")
        self._service = kwds.pop("service")
        self._events_host = kwds.pop("host", gethostname())
        self._call_events = Queue(1000)
        super(Owl, self).__init__(*args, **kwds)
        # Create and start background thread that sends events to Riemann.
        event_worker = Thread(target=self._process_call_metrics)
        event_worker.daemon = True
        event_worker.start()

    def _process_call_metrics(self):
        last_send = datetime.now() - _MAX_SEND_INTERVALL  # first is immediate
        events = []  # buffer for events that should get send
        while True:  # daemon thread, terminates automatically on exit
            events.append(self._call_events.get())  # wait for new event
            # Don't spam Riemann, send blocks of events or wait for some time.
            if (len(events) >= _SEND_LIMIT or
                    last_send < datetime.now() - _MAX_SEND_INTERVALL):
                with self._get_riemann_client() as client:
                    # Prepare events for sending.
                    for event in events:
                        try:
                            client.event(**event)
                        except Exception:
                            pass  # drop event, no connection
                    # Send and clear buffer.
                    try:
                        client.flush()
                    except Exception:
                        pass  # ignore, events lost
                    del events[:]

    def _monitor_end_call(self, env, start, url, status):
        end = time()
        event = {
            "time": timegm(datetime.utcnow().replace(tzinfo=UTC).timetuple()),
            "host": self._events_host,
            "service": self._service,
            "state": status,
            "metric_sint64": int(round((end - start) * 1000)),
            "tags": []  # url]
        }
        try:
            self._call_events.put_nowait(event)
        except Full:
            pass  # silently drop event

    def __call__(self, env, start_response):
        status_recorder = ["000"]

        def _start_response(status, headers, status_recorder=status_recorder):
            start_response(status, headers)
            status_recorder[0] = status

        def call_back(env, start, url, status_recorder=status_recorder):
            self._monitor_end_call(env, start, url, status_recorder[0][:3])

        return IterableWrapper(
            call_back, env, time(), super().__call__(env, _start_response))
