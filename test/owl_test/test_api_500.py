# -*- coding: utf-8 -*-
from falcon.testing import TestResource, TestBase
from falcon import API
from time import sleep


from owl import Owl, api
from unittest.mock import patch


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


class _TestResource(TestResource):
    """ Raises an exception, always.

    Used to test a internal server error response (status 500).
    """

    def on_get(self):
        raise Exception()


class TestAPI500(TestBase):

    def setUp(self):
        super(TestAPI500, self).setUp()
        self.client = _Client()
        self.api = _MonitoredAPI(
            get_riemann_client=lambda: self.client, owl_service="")
        self.api.add_route("/", _TestResource())

    def _wait_for_clear(self):
        for _ in range(100):  # wait a maximum of hundred times
            if self.api._call_events.qsize():
                sleep(0.01)  # not processed, wait
            else:
                return True  # event was taken care of
        return False

    @patch.object(api, "_SEND_LIMIT", 0)  # never group event calls
    def test_server_error(self):
        """ Check that Owl generates a message with a 500 status when the
        server (Falcon API) throws an exception.
        """
        with patch.object(self.client, "event") as event_call:
            with self.assertRaises(Exception):
                self.simulate_request("/")
            self.assertTrue(self._wait_for_clear())  # wait for worker
        self.assertIsNone(self.srmock.status)  # server "crashed"
        _, kwds = event_call.call_args
        self.assertIn("500", kwds.get("tags", []))
