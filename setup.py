# setup.py
# Copyright 2015 Roger Marsh
# Licence: See LICENCE (BSD licence)

from setuptools import setup

if __name__ == '__main__':

    long_description = open('README').read()

    setup(
        name='uci',
        version='0.1.1',
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
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Operating System :: OS Independent',
            'Topic :: Software Development',
            'Intended Audience :: Developers',
            'Development Status :: 4 - Beta',
            ],
        #install_requires=['clientserver==0.1'],
        #dependency_links=[
        #    'http://solentware.co.uk/files/clientserver-0.1.tar.gz'],
        )
