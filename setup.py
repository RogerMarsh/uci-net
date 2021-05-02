# setup.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

from setuptools import setup

if __name__ == '__main__':

    long_description = open('README').read()

    setup(
        name='uci-net',
        version='1.1.1',
        description='Universal Chess Interface client-server conversation',
        author='Roger Marsh',
        author_email='roger.marsh@solentware.co.uk',
        url='http://www.solentware.co.uk',
        package_dir={'uci_net':''},
        packages=[
            'uci_net',
            'uci_net.samples',
            'uci_net.about',
            ],
        package_data={
            'uci_net.about': ['LICENCE', 'CONTACT'],
            },
        long_description=long_description,
        license='BSD',
        classifiers=[
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python :: 3.6',
            'Operating System :: OS Independent',
            'Topic :: Software Development',
            'Intended Audience :: Developers',
            'Development Status :: 4 - Beta',
            ],
        )
