from setuptools import setup, find_packages

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
    url='https://github.com/Lamden/vmnet',
    author='Lamden',
    email='team@lamden.io',
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
    zip_safe=False
)
