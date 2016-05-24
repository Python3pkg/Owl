# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="Owl",
    version="0.2.1",
    license="GPLv2",
    description="Monitor Falcon with Riemann",
    long_description=long_description,
    url="https://github.com/merry-bits/Owl",
    author="merry-bits",
    author_email="merry-bits@users.noreply.github.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: System :: Monitoring",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    keywords=(
        "flacon riemann monitoring measure request time end-point duration"),
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=["pytz"],
    extras_require={
        "test": [
            "falcon==1.0.0", "riemann-client==6.3.0", "mock==1.3.0",
            "nose==1.3.7"
        ]
    },
)
