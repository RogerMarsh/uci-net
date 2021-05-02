# setup.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

from setuptools import setup

if __name__ == '__main__':

    long_description = open('README').read()

    setup(
        name='uci',
        version='1.0',
        description='Universal Chess interface client-server conversation',
        author='Roger Marsh',
        author_email='roger.marsh@solentware.co.uk',
        url='http://www.solentware.co.uk',
        package_dir={'uci':''},
        packages=[
            'uci',
            'uci.samples',
            'uci.about',
            ],
        package_data={
            'uci.about': ['LICENCE', 'CONTACT'],
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
