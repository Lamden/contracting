import unittest, os, sys, importlib
from os import getenv as env

testmodules = [
    'tests.unit.interface',
    'tests.unit.engine',
    'tests.unit.security',
    'tests.unit.contracts',
]

loader = unittest.TestLoader()

for t in testmodules:
    try:
        # If the module defines a suite() function, call it to get the suite.
        suite = loader.discover(t)
        mod = __import__(t, globals(), locals(), ['suite'])
        suitefn = getattr(mod, 'suite')
        suite.addTest(suitefn())
    except (ImportError, AttributeError):
        # else, just load all the test cases from the module.
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
