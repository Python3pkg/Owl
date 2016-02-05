# -*- coding: utf-8 -*-
from threading import Event
from unittest.mock import patch

from falcon import API
from falcon.testing import TestBase
from falcon.testing.resource import TestResource
from riemann_client.client import QueuedClient
from riemann_client.transport import UDPTransport

from pigeon import Pigeon, api


class _MonitoredAPI(Pigeon, API):

    pass


class _Client():

    def event(self):
        pass

    def flush(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _wsgi_read(result):
    """ This is what a WSGI server would/should do to finish of the request
    (timing).
    """
    try:
        for _ in result:
            pass  # send to client
    finally:
        if hasattr(result, 'close'):
            result.close()


class TestAPI(TestBase):

    def setUp(self):
        super().setUp()
        self.client = _Client()
        self.api = _MonitoredAPI(get_riemann_client=lambda: self.client)
        self.api.add_route("/", TestResource())
        self.done_event = Event()

    def _process_call_metrics(self):
        Pigeon._process_call_metrics(self.api)
        self.done_event.set()

    @patch.object(api, "_SEND_LIMIT", 0)  # never group event calls
    def test_monitor_called(self):
        """ Make a call to a dummy resource and check if monitor calls have
        been called.
        """
        with patch.object(self.client, "event") as event_call:
            with patch.object(self.client, "flush") as flush_call:
                with patch.object(
                        self.api, "_process_call_metrics",
                        self._process_call_metrics):
                    _wsgi_read(self.simulate_request("/"))
                    self.assertTrue(self.done_event.wait(1))  # wait for worker
        self.assertEqual(self.srmock.status[:3], "200")
        self.assertTrue(event_call.called)
        self.assertTrue(flush_call.called)

    @patch.object(api, "_SEND_LIMIT", 0)  # never group event calls
    def test_not_conected(self):
        """ Make a call to a dummy resource and check if monitor calls have
        been called.
        """
        with patch.object(
                self.api, "_process_call_metrics",
                self._process_call_metrics):
            with patch.object(
                    self.api, "_get_riemann_client",
                    lambda: QueuedClient(UDPTransport("10.10.10.90"))):
                _wsgi_read(self.simulate_request("/"))
                self.assertTrue(self.done_event.wait(1))  # wait for worker
        self.assertEqual(self.srmock.status[:3], "200")

    @patch.object(api, "_SEND_LIMIT", 0)  # never group event calls
    def test_not_conected_post(self):
        """ Make a call to a dummy resource and check if monitor calls have
        been called.
        """
        with patch.object(
                self.api, "_process_call_metrics",
                self._process_call_metrics):
            with patch.object(
                    self.api, "_get_riemann_client",
                    lambda: QueuedClient(UDPTransport("10.10.10.90"))):
                _wsgi_read(self.simulate_request("/", method="POST"))
                self.assertTrue(self.done_event.wait(1))  # wait for worker
        self.assertEqual(self.srmock.status[:3], "405")
