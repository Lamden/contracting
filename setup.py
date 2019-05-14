from setuptools import setup, find_packages
from setuptools.extension import Extension
from distutils.command.build_ext import build_ext, CCompilerError, DistutilsExecError, DistutilsPlatformError
import os
from distutils import errors
import sys

major = 0

__version__ = '0.1.1'

requirements = [
    'redis==2.10.6',
    'python-dotenv==0.9.1',
    'ujson==1.35',
    'autopep8==1.4.3',
    'coloredlogs==10.0',
    'transitions==0.6.9',
    'astor==0.7.1'
]

ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)


class BuildFailed(Exception):
    def __init__(self):
        self.cause = sys.exc_info()[1]  # work around py 2/3 different syntax


class ve_build_ext(build_ext):
    """Build C extensions, but fail with a straightforward exception."""

    def run(self):
        """Wrap `run` with `BuildFailed`."""
        try:
            build_ext.run(self)
        except errors.DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        """Wrap `build_extension` with `BuildFailed`."""
        try:
            # Uncomment to test compile failure handling:
            #   raise errors.CCompilerError("OOPS")
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()
        except ValueError as err:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(err):    # works with both py 2/3
                raise BuildFailed()
            raise

setup(
    name='contracting',
    version=__version__,
    description='Python-based smart contract language and interpreter.',
    packages=find_packages(),
    install_requires=requirements,
    url='https://github.com/Lamden/contracting',
    author='Lamden',
    author_email='team@lamden.io',
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
    zip_safe=True,
    include_package_data=True,
    ext_modules=[
        Extension('contracting.execution.metering.tracer', sources = ['contracting/execution/metering/tracer.c']),
    ],
    cmdclass={
        'build_ext': ve_build_ext,
    },
)
