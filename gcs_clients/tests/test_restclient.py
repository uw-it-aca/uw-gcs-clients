# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import json
from datetime import datetime, timedelta
from unittest import TestCase
from commonconf import override_settings
from gcs_clients import RestclientGCSClient
from gcs_clients.restclient import CachedHTTPResponse
from mock import MagicMock, patch


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
            "a": None, "b": "test", "c": [(1, 2), (3, 4)]
        }
        self.test_status = 200
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
        # mock blob
        mock_blob = MagicMock()
        self.mock_blob = mock_blob
        # mock client
        rest_client = RestclientGCSClient()
        rest_client.client._bucket = MagicMock()
        rest_client.client._bucket.get_blob = MagicMock(return_value=mock_blob)
        rest_client.client._client = MagicMock()
        self.client = rest_client

    @patch('gcs_clients.RestclientGCSClient._create_key',
           return_value="abc/api/v1/test")
    @patch('gcs_clients.GCSBucketClient.get',
           return_value=(
            '{"status": 200,'
            '"headers": "\'Content-Disposition\': '
            '\'attachment; filename=\'fname.ext\'\'",'
            '"data": {"key1": "value1", "key2": "value2"}}'))
    def test_getCache(self, mock_get, mock_create_key):
        response = self.client.getCache("abc", "/api/v1/test")
        mock_create_key.assert_called_once_with("abc", "/api/v1/test")
        mock_get.assert_called_once_with("abc/api/v1/test", expire=0)
        self.assertIn("response", response)
        self.assertEqual(CachedHTTPResponse, type(response["response"]))

    @patch('gcs_clients.RestclientGCSClient._create_key',
           return_value="abc/api/v1/test")
    def test_getCache_expired(self, mock_create_key):
        self.mock_blob.custom_time = \
            datetime.utcnow() - timedelta(seconds=11)
        self.mock_blob.download_as_string = MagicMock(
            return_value='{'
            '"status": 200,'
            '"headers": "\'Content-Disposition\': \'attachment; '
            'filename=\'fname.ext\'\'",'
            '"data": {"key1": "value1", "key2": "value2"}'
            '}')
        # expired
        self.client.get_cache_expiration_time = MagicMock(return_value=10)
        response = self.client.getCache("abc", "/api/v1/test")
        self.assertEqual(response, None)
        # not expired
        self.client.get_cache_expiration_time = MagicMock(return_value=30)
        response = self.client.getCache("abc", "/api/v1/test")
        mock_create_key.assert_called_with("abc", "/api/v1/test")
        self.assertIn("response", response)
        self.assertEqual(CachedHTTPResponse, type(response["response"]))

    @patch('gcs_clients.GCSBucketClient.delete')
    @patch('gcs_clients.RestclientGCSClient._create_key',
           return_value="abc/api/v1/test")
    def test_deleteCache(self, mock_create_key, mock_delete):
        self.client.deleteCache("abc", "/api/v1/test")
        mock_create_key.assert_called_once_with("abc", "/api/v1/test")
        mock_delete.assert_called_once_with("abc/api/v1/test")

    @patch('gcs_clients.GCSBucketClient.set')
    @patch('gcs_clients.RestclientGCSClient._create_key',
           return_value="abc/api/v1/test")
    def test_updateCache(self, mock_create_key, mock_set):
        mock_data = MagicMock()
        with patch.object(self.client,
                          '_format_data') as mock_format_data:
            mock_format_data.return_value = mock_data
            self.client.updateCache(
                "abc", "/api/v1/test", mock_data)
            mock_create_key.assert_called_once_with("abc", "/api/v1/test")
            mock_set.assert_called_once_with("abc/api/v1/test", mock_data,
                                             expire=0)

    def test_create_key(self):
        self.assertEqual(self.client._create_key("abc", "/api/v1/test"),
                         "abc/api/v1/test")
        long_url = "/api/v1/{}".format("x" * 250)
        self.assertEqual(self.client._create_key("abc", long_url),
                         "abc{}".format(long_url))
        self.assertEqual(
            self.client._create_key("xyz", "/api/v1/test?p1=true&p2=10"),
            "xyz/api/v1/test?p1=true&p2=10")

    def test_format_data(self):
        self.test_response = CachedHTTPResponse(
            status=200,
            data=b'{"a": 1, "b": "test", "c": []}',
            headers={"Content-Disposition": "attachment; filename='fname.ext'"}
        )
        formatted_response = self.client._format_data(self.test_response)
        self.assertEqual(
            formatted_response,
            json.dumps(
                {"status": 200,
                 "headers": {"Content-Disposition": "attachment; "
                             "filename=\'fname.ext\'"},
                 "data": "{\"a\": 1, \"b\": \"test\", \"c\": []}"}
            ))
