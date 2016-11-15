#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) The mclone project
# This code is distributed under the two-clause BSD License.

import codecs
import os
import re
import sys

from setuptools import find_packages, setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version():
    from mclone import version
    return version.__version__


def clean_readme(fname):
    """Cleanup README.rst for proper PyPI formatting."""
    with codecs.open(fname, 'r', 'utf-8') as f:
        return ''.join(
            re.sub(r':\w+:`([^`]+?)( <[^<>]+>)?`', r'``\1``', line)
            for line in f
            if not (line.startswith('.. currentmodule') or line.startswith('.. toctree'))
        )


PACKAGE = 'mclone'


setup(
    name=PACKAGE,
    version=get_version(),
    author="Raphaël Barrois",
    author_email='raphael.barrois_%s@polytechnique.org' % PACKAGE,
    description="Simple framework for inter-system, mono-source / multi-target data replication",
    long_description=clean_readme('README.rst'),
    license='BSD',
    keywords=['mclone', 'replication'],
    url='https://github.com/rbarrois/%s' % PACKAGE,
    install_requires=[
    ],
    setup_requires=[
        'setuptools>=1',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    classifiers=[
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
)
