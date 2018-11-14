from setuptools import setup, find_packages
from setuptools.extension import Library

__version__ = '0.1.0'

setup(
    name='seneca',
    version=__version__,
    description='Python-based smart contract language and interpreter.',
    entry_points={
        'console_scripts': ['seneca=seneca.cli:main'],
    },
    packages=find_packages(),
    install_requires=open('requirements.txt').readlines(),
    url='https://github.com/Lamden/seneca',
    author='Lamden',
    author_email='team@lamden.io',
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
    zip_safe=False,
    ext_modules=[
        Library('tracer', sources = ['seneca/libs/metering/tracer.c'])
    ]
)
