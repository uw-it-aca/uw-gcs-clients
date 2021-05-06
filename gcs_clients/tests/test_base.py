# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from unittest import TestCase, skipUnless
from commonconf import settings, override_settings
from gcs_clients import GCSClient
import os


class TestGCSClient(TestCase):
    def setUp(self):
        self.client = GCSClient()

    def test_invalid_method(self):
        self.assertRaises(AttributeError, self.client.fake)

    def test_default_settings(self):
        client = self.client.client
        self.assertEqual(client.replace, False)
        self.assertEqual(client.timeout, 5)
        self.assertEqual(client.num_retries, 3)
