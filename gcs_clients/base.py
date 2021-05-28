# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import logging
import socket

from commonconf import settings
from datetime import datetime, timezone
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError
from google.cloud.exceptions import NotFound
from io import IOBase
from threading import local


class GCSClient():
    """
    A settings-based wrapper around GCSBucketClient client. Ensures that every
    request is processed by the same cache client.
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
        """
        Create a new client object instance with settings mapped from
        environment settings
        """
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
        self.bucket_name = bucket_name
        self.replace = replace
        self.timeout = timeout
        self.num_retries = num_retries
        self._bucket = None
        self._client = None

    @property
    def client(self):
        """
        Retreive GCS client object
        """
        if self._client is None:
            client = storage.Client()
            self._client = client
            return self._client
        else:
            return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @property
    def bucket(self):
        """
        Retreive GCS bucket object
        """
        if self._bucket is None:
            bucket = self.client.get_bucket(self.bucket_name)
            self._bucket = bucket
            return self._bucket
        else:
            return self._bucket

    @bucket.setter
    def bucket(self, value):
        self._bucket = value

    def delete(self, url_key):
        """
        Delete content matching url_key from GCS bucket

        :param url_key: URL response to cache
        :type url_key: str
        """
        try:
            self.bucket.get_blob(url_key).delete(timeout=self.timeout)
        except NotFound as ex:
            logging.error("gcp {}: {}".format(url_key, ex))
            raise

    def get(self, url_key, expire=0):
        """
        Download content from a GCS bucket as a string

        :param url_key: URL response to cache
        :type url_key: str
        :param expire: Number of seconds until the item is expired from the
            cache, or 0 for no expiry (the default).
        :type expire: int (optional, default 0)
        """
        try:
            blob = self.bucket.get_blob(url_key)
            if blob:
                creation_time = blob.custom_time
                if creation_time:
                    creation_time = creation_time.replace(tzinfo=timezone.utc)
                    time_since_creation = \
                        (datetime.now(timezone.utc) - creation_time) \
                        .total_seconds()
                    if (round(time_since_creation, 2) <=
                            expire or expire == 0):
                        content = blob.download_as_string(timeout=self.timeout)
                        return content
                    else:
                        return None  # expired content
        except NotFound as ex:
            logging.error("gcp {}: {}".format(url_key, ex))
            raise

    def set(self, url_key, content, expire=0):
        """
        Upload a string or file-like object contents to GCS bucket

        :param url_key: URL response to cache
        :type url_key: str
        :param content: Content to cache
        :type content: str or file object
        :param expire: If None, don't update the cache otherwise upload to the
            cache, the default
        :type expire: int or None (optional, default update)
        """
        if expire is not None:
            blob = None
            if self.replace is False:
                blob = self.bucket.get_blob(url_key)
            if not blob:
                blob = self.bucket.blob(url_key)
            blob.custom_time = datetime.now(timezone.utc)
            if isinstance(content, IOBase):
                blob.upload_from_file(content,
                                      num_retries=self.num_retries,
                                      timeout=self.timeout)
            else:
                blob.upload_from_string(str(content),
                                        num_retries=self.num_retries,
                                        timeout=self.timeout)
