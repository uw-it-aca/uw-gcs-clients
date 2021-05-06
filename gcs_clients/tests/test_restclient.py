# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from unittest import TestCase, skipUnless
from commonconf import settings, override_settings
from gcs_clients import GCSClient, RestclientGCSClient
from gcs_clients.restclient import CachedHTTPResponse
import os



class MockClientCachePolicy(RestclientGCSClient):
    def get_cache_expiration_time(self, service, url, status=None):
        if service == "abc":
            if status == 404:
                return None
            return 60
        return 0


class MockClientCachePolicyNone(RestclientGCSClient):
    def get_cache_expiration_time(self, service, url, status=None):
        return None


class TestCachedHTTPResponse(TestCase):
    def setUp(self):
        self.test_headers = {
            "Content-Disposition": "attachment; filename='name.ext'"
        }
        self.test_data = {
            "a": None, "b": b"test", "c": [(1, 2), (3, 4)]
        }
        self.test_status = 201
        self.response = CachedHTTPResponse(
            data=self.test_data,
            headers=self.test_headers,
            status=self.test_status)

    def test_read(self):
        empty = CachedHTTPResponse()
        self.assertEqual(empty.read(), None)

        self.assertEqual(self.response.read(), self.test_data)

    def test_getheader(self):
        empty = CachedHTTPResponse()
        self.assertEqual(empty.getheader("cache-control"), "")

        self.assertEqual(self.response.getheader("content-disposition"),
                         "attachment; filename='name.ext'")


class TestCachePolicy(TestCase):

    def test_get_cache_expiration_time(self):
        self.client = MockClientCachePolicy()
        self.assertEqual(
            self.client.get_cache_expiration_time("xyz", "/api/v1/test"), 0)

        self.assertEqual(
            self.client.get_cache_expiration_time(
                "abc", "/api/v1/test", 200), 60)

        self.assertEqual(
            self.client.get_cache_expiration_time(
                "abc", "/api/v1/test", 404), None)

    @override_settings(RESTCLIENTS_GCS_DEFAULT_EXPIRY=3600)
    def test_default_cache_expiration_time(self):
        self.client = RestclientGCSClient()
        self.assertEqual(
            self.client.get_cache_expiration_time(
                "abc", "/api/v1/test", 200), 3600)


class TestRestclientGCSClient(TestCase):
    def setUp(self):
        self.client = RestclientGCSClient()

    def test_create_key(self):
        self.assertEqual(self.client._create_key("abc", "/api/v1/test"),
                         "abc-8157d24840389b1fec9480b59d9db3bde083cfee")

        long_url = "/api/v1/{}".format("x" * 250)
        self.assertEqual(self.client._create_key("abc", long_url),
                         "abc-61fdd52a3e916830259ff23198eb64a8c43f39f2")

    def test_format_data(self):
        self.test_response = CachedHTTPResponse(
            status=200,
            data={"a": 1, "b": b"test", "c": []},
            headers={"Content-Disposition": "attachment; filename='fname.ext'"}
        )
        self.assertEqual(self.client._format_data(self.test_response), {
            "status": self.test_response.status,
            "headers": self.test_response.headers,
            "data": self.test_response.data
        })
