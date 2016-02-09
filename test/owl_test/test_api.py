# -*- coding: utf-8 -*-
from time import sleep
from unittest.mock import patch

from falcon import API
from falcon.testing import TestBase
from falcon.testing.resource import TestResource
from riemann_client.client import QueuedClient
from riemann_client.transport import UDPTransport

from owl import Owl, api


class _MonitoredAPI(Owl, API):

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
        self.api = _MonitoredAPI(
            owl_get_riemann_client=lambda: self.client, owl_service="")
        self.api.add_route("/", TestResource())

    def _wait_for_clear(self):
        for _ in range(100):  # wait a maximum of hundred times
            if self.api._call_events.qsize():
                sleep(0.01)  # not processed, wait
            else:
                return True  # event was taken care of
        return False

    @patch.object(api, "_SEND_LIMIT", 0)  # never group event calls
    def test_monitor_called(self):
        """ Make a call to a dummy resource and check if monitor calls have
        been called.
        """
        with patch.object(self.client, "event") as event_call:
            with patch.object(self.client, "flush") as flush_call:
                _wsgi_read(self.simulate_request("/"))
                self.assertTrue(self._wait_for_clear())  # wait for worker
        self.assertEqual(self.srmock.status[:3], "200")
        self.assertTrue(event_call.called)
        self.assertTrue(flush_call.called)

    @patch.object(api, "_SEND_LIMIT", 0)  # never group event calls
    def test_not_conected(self):
        """ Make a call to a dummy resource and check if monitor calls have
        been called.
        """
        with patch.object(
                self.api, "_get_riemann_client",
                lambda: QueuedClient(UDPTransport("10.10.10.90"))):
            _wsgi_read(self.simulate_request("/"))
            self.assertTrue(self._wait_for_clear())  # wait for worker
        self.assertEqual(self.srmock.status[:3], "200")

    @patch.object(api, "_SEND_LIMIT", 0)  # never group event calls
    def test_not_conected_post(self):
        """ Make a call to a dummy resource and check if monitor calls have
        been called.
        """
        with patch.object(
                self.api, "_get_riemann_client",
                lambda: QueuedClient(UDPTransport("10.10.10.90"))):
            _wsgi_read(self.simulate_request("/", method="POST"))
            self.assertTrue(self._wait_for_clear())  # wait for worker
        self.assertEqual(self.srmock.status[:3], "405")
