# uw-gcs-clients

[![Build Status](https://github.com/uw-it-aca/uw-gcs-clients/workflows/tests/badge.svg?branch=master)](https://github.com/uw-it-aca/uw-gcs-clients/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/uw-gcs-clients/badge.svg?branch=master)](https://coveralls.io/github/uw-it-aca/uw-gcs-clients?branch=master)
[![PyPi Version](https://img.shields.io/pypi/v/uw-gcs-clients.svg)](https://pypi.python.org/pypi/uw-gcs-clients)
![Python versions](https://img.shields.io/pypi/pyversions/uw-gcs-clients.svg)

A wrapper around the Google Cloud Storage (GCS) storage client (https://googleapis.dev/python/storage/latest/), configured to support connection pooling with logging to a GCS storage bucket.

Installation:

    pip install uw-gcs-clients

To use this client, you'll need these settings in your application or script:

    # GCS bucket name
    GCS_BUCKET_NAME=""

Optional settings:

    GCS_REPLACE=False  # replace contents if already exists
    GCS_TIMEOUT=5  # request timeout in seconds
    GCS_NUM_RETRIES=3  # number of request retries

Additionally, a base path environment may be specified. It gets appended to the beginning of the api url path that's saved in the GCS bucket.

    GCS_BASE_PATH="/some/base/path/"

or in Python:

    import os
    os.environ["GCS_BASE_PATH"] = "/some/base/path/"
    
See examples for usage. Pull requests welcome.
