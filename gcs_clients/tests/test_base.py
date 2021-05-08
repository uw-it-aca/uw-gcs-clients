# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from unittest import TestCase
from io import StringIO
from gcs_clients import GCSClient
from mock import MagicMock, patch


def get_default_client():
    # mock blob
    mock_blob = MagicMock()
    mock_blob.upload_from_file = MagicMock(return_value=True)
    mock_blob.download_as_string = \
        MagicMock(
            return_value=(
                '{'
                '"status": 200,'
                '"headers": "\'Content-Disposition\': \'attachment; '
                'filename=\'fname.ext\'\'",'
                '"data": {"key1": "value1", "key2": "value2"}'
                '}')
        )
    # mock client
    gcs_client = GCSClient()
    gcs_client.client._bucket = MagicMock()
    gcs_client.client._bucket.get_blob = MagicMock(return_value=mock_blob)
    gcs_client.client._client = MagicMock()
    return gcs_client


class TestGCSClient(TestCase):
    def setUp(self):
        self.gcs_client = get_default_client()

    def test_invalid_method(self):
        self.assertRaises(AttributeError, self.gcs_client.fake)

    def test_default_settings(self):
        client = self.gcs_client.client
        self.assertEqual(client.replace, False)
        self.assertEqual(client.bucket_name, '')
        self.assertEqual(client.timeout, 5)
        self.assertEqual(client.num_retries, 3)


class TestGCSBucketClient(TestCase):
    def setUp(self):
        self.gcs_client = get_default_client()

    def test_get(self):
        self.assertEqual(
            self.gcs_client.get("/api/v1/test"),
            {
                'status': 200,
                'headers': "\'Content-Disposition\': \'attachment; "
                "filename=\'fname.ext\'\'",
                'data': {'key1': 'value1', 'key2': 'value2'}
            }
        )

    def test_delete(self):
        with patch.object(self.gcs_client.client._bucket.get_blob(),
                          'delete') as mock_delete:
            self.gcs_client.delete("/api/v1/test")
        mock_delete.assert_called_once_with(
            timeout=self.gcs_client.client.timeout)

    def test_set_str(self):
        # set with str
        content = ('{"status": 200,'
                   '"headers": "\'Content-Disposition\': \'attachment; "'
                   '"filename=\'fname.ext\'\'",'
                   '"data": {"key1": "value1", "key2": "value2"}}')
        with patch.object(self.gcs_client.client._bucket.get_blob(),
                          'upload_from_file') as mock_upload_from_file:
            with patch.object(self.gcs_client.client._bucket.get_blob(),
                              'upload_from_string') as mock_upload_from_string:
                self.gcs_client.set("/api/v1/test", content)
        mock_upload_from_string.assert_called_once_with(
            content,
            num_retries=self.gcs_client.client.num_retries,
            timeout=self.gcs_client.client.timeout)
        assert not mock_upload_from_file.called

    def test_set_fileobj(self):
        # set with StringIO
        content = ('{"status": 200,'
                   '"headers": "\'Content-Disposition\': \'attachment; "'
                   '"filename=\'fname.ext\'\'",'
                   '"data": {"key1": "value1", "key2": "value2"}}')
        content = StringIO(content)
        with patch.object(self.gcs_client.client._bucket.get_blob(),
                          'upload_from_file') as mock_upload_from_file:
            with patch.object(self.gcs_client.client._bucket.get_blob(),
                              'upload_from_string') as mock_upload_from_string:
                self.gcs_client.set("/api/v1/test", content)
        mock_upload_from_file.assert_called_once_with(
            content,
            num_retries=self.gcs_client.client.num_retries,
            timeout=self.gcs_client.client.timeout)
        assert not mock_upload_from_string.called
