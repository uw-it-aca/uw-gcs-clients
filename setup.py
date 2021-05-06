import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/uw-gcs-clients>`_.
"""

version_path = 'gcs_clients/VERSION'
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

url = "https://github.com/uw-it-aca/uw-gcs-clients"
setup(
    name='uw-gcs-clients',
    version=VERSION,
    packages=['gcs_clients'],
    author="UW-IT AXDD",
    author_email="aca-it@uw.edu",
    include_package_data=True,
    install_requires=[
        'commonconf~=1.0',
        'google-cloud-storage>=1.37.1,<2.0',
        'google-api-core>=1.26.3,<2.0',
        'mock',
    ],
    license='Apache License, Version 2.0',
    description=('Google Cloud Storage (GCS) Clients'),
    long_description=README,
    url=url,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6'
    ],
)
