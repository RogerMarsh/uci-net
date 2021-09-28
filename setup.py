# setup.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)
"""uci-net setup file."""

from setuptools import setup

if __name__ == "__main__":

    long_description = open("README").read()

    setup(
        name="uci-net",
        version="1.2.2",
        description="Universal Chess Interface client-server conversation",
        author="Roger Marsh",
        author_email="roger.marsh@solentware.co.uk",
        url="http://www.solentware.co.uk",
        packages=[
            "uci_net",
            "uci_net.samples",
        ],
        long_description=long_description,
        license="BSD",
        classifiers=[
            "License :: OSI Approved :: BSD License",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Operating System :: OS Independent",
            "Topic :: Software Development",
            "Intended Audience :: Developers",
            "Development Status :: 3 - Alpha",
        ],
    )
