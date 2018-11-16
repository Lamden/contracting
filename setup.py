from setuptools import setup, find_packages
from setuptools.extension import Extension
import os

major = 0

def get_version_number():
    if os.getenv('CIRCLECI'):
        minor, patch = divmod(int(os.getenv('CIRCLE_BUILD_NUM')), 360)
        ver = '{}.{}.{}'.format(major, minor, patch)
        print('CircleCI will now upload version "{}"'.format(ver))
        return ver
    else:
        return '{}.1.0'.format(major)

__version__ = get_version_number()

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
        Extension('tracer', sources = ['seneca/libs/metering/tracer.c'])
    ]
)
