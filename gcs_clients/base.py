# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import socket

from commonconf import settings
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError
from io import StringIO
from mock import MagicMock
from threading import local


class GCSClient():
    """
    A settings-based wrapper around GCSBucketClient client
    """
    def __init__(self):
        self._local = local()

    def __getattr__(self, name, *args, **kwargs):
        """
        Pass unshimmed method calls through to the client, and add logging
        for errors.
        """
        def handler(*args, **kwargs):
            try:
                return getattr(self.client, name)(*args, **kwargs)
            except (GoogleAPIError, socket.gaierror) as ex:
                logging.error("gcp {}: {}".format(name, ex))
            except AttributeError:
                raise
        return handler

    @property
    def client(self):
        if not hasattr(self._local, "client"):
            self._local.client = self.__client__()
        return self._local.client

    def __client__(self):
        return GCSBucketClient(
            getattr(settings, "GCS_BUCKET_NAME", None),
            replace=getattr(settings, "GCS_REPLACE", False),
            timeout=getattr(settings, "GCS_TIMEOUT", 5),
            num_retries=getattr(settings, "GCS_NUM_RETRIES", 3))


class GCSBucketClient():
    """
    Cloud storage bucket upload/download using
    google.cloud.storage.Client
    """

    def __init__(self, bucket_name, replace=False, timeout=5, num_retries=3):
        """
        :param bucket_name: Name of the bucket to read/write from
        :type bucket_name: str
        :param replace: Whether to replace file contents, defaults to False
        :type replace: bool (optional)
        :param timeout: Request timeout in seconds, defaults to 5
        :type timeout: bool (optional)
        :param num_retries: Number of request retries, defaults to 3
        :type num_retries: int (optional)
        """
        self.client = self._get_client()
        self.bucket = self._get_bucket(bucket_name)
        self.replace = replace
        self.timeout = timeout
        self.num_retries = num_retries

    def _get_client(self):
        """
        Retreive GCS client object
        """
        env = os.getenv("ENV")
        if env == "localdev" or not env:
            # mock the GCS storage client on localdev
            mock_client = MagicMock()
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_blob.upload_from_file = MagicMock(return_value=True)
            mock_bucket.get_blob = MagicMock(return_value=mock_blob)
            mock_client.get_bucket = mock_bucket
            client = mock_client
        else:
            client = storage.Client()
        return client

    def _get_bucket(self, bucket_name):
        """
        Retreive GCS bucket object

        :param bucket_name: Name of the bucket to read/write from
        :type bucket_name: str
        """
        return self.client.get_bucket(bucket_name)

    def upload(self, url_key, content):
        """
        Upload a string to GCS bucket

        :param url_key: URL response to cache 
        :type url_key: str
        :param content: File contents to upload
        :type content: str
        """

        blob = None
        if self.replace is False:
            blob = self.bucket.get_blob(url_key)
        if not blob:
            blob = self.bucket.blob(url_key)
        if isinstance(content, str):
            blob.upload_from_string(content, num_retries=self.num_retries,
                                    timeout=self.timeout)
        elif isinstance(content, StringIO):
            blob.upload_from_file(content, num_retries=self.num_retries,
                                timeout=self.timeout)

    def get(self, url_key):
        """
        Download content from a GCS bucket as a string

        :param url_key: URL response to cache 
        :type url_key: str
        """
        return self.bucket.get_blob(url_key).download_as_string()

    def set(self, url_key, content):
        """
        Upload a string or file-like object contents to GCS bucket

        :param url_key: URL response to cache 
        :type url_key: str
        """
        self.upload(url_key, content)
