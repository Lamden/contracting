from setuptools import setup, find_packages
from setuptools.extension import Extension
import os

major = 0

def get_version_number():
    if os.getenv('CIRCLECI'):
        minor, patch = divmod(int(os.getenv('CIRCLE_BUILD_NUM')), 360)
        ver = '{}.{}.{}'.format(major, minor, patch)
        return ver
    else:
        return '{}.1.0'.format(major)

__version__ = get_version_number()

print('#' * 128)
print('\n    VERSION = {}\n'.format(__version__))
print('#' * 128)

dev_requirements = [
    'coloredlogs==10.0',
    'coverage==4.5.1',
    'pynacl',
    # WARNING replace dateutil!
    'python-dateutil==2.7.3',
    'scipy==1.1.0',
    'numpy==1.15.4'
]
requirements = [
    'redis==2.10.6',
    'python-dotenv==0.9.1',
    'ujson==1.35'
]

setup(
    name='seneca',
    version=__version__,
    description='Python-based smart contract language and interpreter.',
    entry_points={
        'console_scripts': ['seneca=seneca.cli:main'],
    },
    packages=find_packages(),
    install_requires=requirements + dev_requirements,
    url='https://github.com/Lamden/seneca',
    author='Lamden',
    author_email='team@lamden.io',
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
    zip_safe=False,
    include_package_data=True,
    ext_modules=[
        Extension('seneca.libs.metering.tracer', sources = ['seneca/libs/metering/tracer.c'])
    ]
)
