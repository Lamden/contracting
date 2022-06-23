from setuptools import setup, find_packages
from setuptools.extension import Extension
from distutils.command.build_ext import build_ext, CCompilerError, DistutilsExecError, DistutilsPlatformError
from distutils import errors
import sys, subprocess
from sys import platform

major = 0

__version__ = '1.0.5.2'

requirements = ['astor', 'pymongo', 'autopep8', 'stdlib_list', 'h5py==3.1.0', 'lmdb']

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

def pkgconfig(package):
    flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}
    res = {}

    if platform == "linux" or platform == "linux2":
        output = subprocess.getoutput('pkg-config --cflags --libs {}'.format(package))
        for token in output.strip().split():
            res.setdefault(flag_map.get(token[:2]), []).append(token[2:])

    elif platform == "darwin":
        res['libraries'] = ['hdf5']
        output = subprocess.getoutput('brew list hdf5')
        print(output)
        if 'Error: No sach keg:' in output:
            raise ModuleNotFoundError('Install HDF5 package using brew. "brew install hdf5"')
        for token in output.strip().split():
            if "/include/" in token:
                res['include_dirs'] = [token.split('/include/')[0] + '/include/']
            if "/lib/" in token:
                res['library_dirs'] = [token.split('/lib/')[0] + '/lib/']

    elif platform == "win32":
        raise NotImplemented("Cannot install on Windows")

    return res

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
        Extension('contracting.execution.metering.tracer', sources=['contracting/execution/metering/tracer.c']),
        Extension('contracting.db.hdf5.h5c', sources=['contracting/db/hdf5/h5c.c'], **pkgconfig('hdf5'))
    ],
    cmdclass={
        'build_ext': ve_build_ext,
    },
)
