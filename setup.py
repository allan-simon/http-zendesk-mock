#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

setup(
    name="mock_zendesk",
    version="0.1",
    description="Mock zendesk.com service and related utilities",
    install_requires=["requests"],
    packages=find_packages(),
)
