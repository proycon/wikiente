#! /usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import print_function

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname),'r',encoding='utf-8').read()

setup(
    name = "WikiEnte",
    version = "0.1.0", #also edit in __init__.py
    author = "Maarten van Gompel",
    author_email = "proycon@anaproy.nl",
    description = ("Entity extraction using DBPedia through spotlight"),
    license = "GPL",
    keywords = "nlp computational_linguistics entities wikipedia dbpedia linguistics",
    url = "https://github.com/proycon/wikiente",
    packages=['wikiente'],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    zip_safe=False,
    include_package_data=True,
    #package_data = { 'babelente': ['babelente.config.yml'] },
    install_requires=[ 'pyspotlight','folia >= 2.1.3'],
    entry_points = {   'console_scripts': [ 'wikiente = wikiente.wikiente:main' ] }
)
