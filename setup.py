#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages


setup(
    name="Pigeon",
    version="0.0.1",
    license="GPLv2",
    description="Monitor Falcon with Riemann",
    url="https://github.com/merry-bits/Pigeon",
    classifiers=[
        "Framework :: Falcon",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Topic :: System :: Monitoring",
        "Programming Language :: Python :: 3.4",
    ],
    keywords="flacon riemann monitoring measure call end-point duration",
    packages=find_packages("src"),
    package_dir = {"": "src"},
    install_requires=["pytz", "riemann-client>=6.1.3"],
    package_dir={"pigeon": "src/pigeon"},
    extras_require={
        "falcon": ["falcon>=0.3.0"],
    },
)
