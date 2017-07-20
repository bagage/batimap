#!/usr/bin/env python3

"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

setup(
    name='batimap',

    version='0.0.1',

    description='État de l\'intégration du cadastre dans OSM',
    long_description='Permet d\'interroger et d\'importer le bâti cadastral dans OSM',

    url='https://github.com/bagage/cadastre-conflation',

    author='Gautier Pelloux-Prayer',
    author_email='gautier@damsy.net',

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='openstreetmap overpass postgis',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    install_requires=['colorlog', 'colour', 'geojson', 'overpass',
                      'psycopg2', 'pygeoj', 'requests', 'argcomplete', 'tqdm'],

    package_data={
        'cadastre': ['code-cadastre.csv'],
    },

    entry_points={
        'console_scripts': [
            'batimap=batimap:batimap',
        ],
    },
)
