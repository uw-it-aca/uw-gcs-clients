# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import logging
import json
import os
from commonconf import settings
from gcs_clients import GCSClient
from google.api_core.exceptions import GoogleAPIError
from urllib.parse import urlparse


class CachedHTTPResponse():
    """
    Represents an HTTPResponse, implementing methods as needed.
    """
    def __init__(self, **kwargs):
        self.headers = kwargs.get("headers", {})
        self.status = kwargs.get("status")
        self.data = kwargs.get("data")

    def read(self):
        return self.data

    def getheader(self, val, default=''):
        for header in self.headers:
            if val.lower() == header.lower():
                return self.headers[header]
        return default


class RestclientGCSClient(GCSClient):

    def getCache(self, service, url, headers=None):
        expire = self.get_cache_expiration_time(service, url)
        if expire is not None:
            data = self.get(self._create_key(service, url,
                                             base_path=self.get_base_path()),
                            expire=expire,)
            if data:
                parsed_data = json.loads(data)
                return {"response": CachedHTTPResponse(**parsed_data)}

    def deleteCache(self, service, url):
        return self.delete(self._create_key(service, url,
                                            base_path=self.get_base_path()))

    def updateCache(self, service, url, response):
        expire = self.get_cache_expiration_time(service, url, response.status)
        if expire is not None:
            key = self._create_key(service, url,
                                   base_path=self.get_base_path())
            data = self._format_data(response)
            try:
                # Bypass the shim client to log the original URL if needed.
                self.client.set(key, data, expire=expire)
            except (GoogleAPIError, ConnectionError) as ex:
                logging.error("gcs set: {}, url: {}".format(ex, url))

    processResponse = updateCache

    def get_cache_expiration_time(self, service, url, status=None):
        """
        Overridable method for setting the cache expiration per service, url,
        and response status.  Valid return values are:
          * Number of seconds until the item is expired from the cache,
          * Zero, for no expiry,
          * None, indicating that the item should not be cached.
        """
        return getattr(settings, "RESTCLIENTS_GCS_DEFAULT_EXPIRY", 0)

    def get_base_path(self):
        """
        Overridable method for setting the base path to be appended to
        data written to the GCS bucket. Defaults to ''.
        """
        return os.getenv("GCS_BASE_PATH", default='')

    @staticmethod
    def _create_key(service, url, base_path=''):
        parsed = urlparse(url)
        base_path = base_path.strip("/")
        parsed_url_path = parsed.path.lstrip("/")
        path = "/".join([base_path, service, parsed_url_path]).lstrip("/")
        query = parsed.query
        if path and query:
            url_key = "?".join([path, query])
        else:
            url_key = path
        return url_key

    @staticmethod
    def _format_data(response):
        # This step is needed because HTTPHeaderDict isn't serializable
        headers = {}
        if response.headers is not None:
            for header in response.headers:
                headers[header] = response.getheader(header)
        return json.dumps({
            "status": response.status,
            "headers": headers,
            "data": response.data.decode('utf-8')
        })
