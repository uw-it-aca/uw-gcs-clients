# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from unittest import TestCase, skipUnless
from commonconf import settings, override_settings
from gcs_clients import GCSClient, GCSBucketClient
from mock import MagicMock, patch
import os


class TestGCSClient(TestCase):
    def setUp(self):
        # mock blob
        mock_blob = MagicMock()
        mock_blob.upload_from_file = MagicMock(return_value=True)
        # mock bucket
        mock_bucket = MagicMock()
        mock_bucket.get_blob = MagicMock(return_value=mock_blob)
        # mock client
        client = GCSClient()
        client.client._get_bucket = MagicMock(return_value=mock_bucket)
        client.client._get_client = MagicMock()
        self.client = client

    def test_invalid_method(self):
        self.assertRaises(AttributeError, self.client.fake)

    def test_default_settings(self):
        client = self.client.client
        self.assertEqual(client.replace, False)
        self.assertEqual(client.bucket_name, '')
        self.assertEqual(client.timeout, 5)
        self.assertEqual(client.num_retries, 3)
