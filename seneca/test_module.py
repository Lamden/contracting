#!/usr/bin/env python3

import argparse
import importlib
import re
import sys
import os

print('>>>>> Starting test module')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


parser = argparse.ArgumentParser()
parser.add_argument("--path", help="Path of the module you want to test.")
conf = parser.parse_args()

def run_tests():
    pass

if hasattr(conf, 'path'):
    if conf.path == __file__:
        pass
    else:
        module = re.sub('\/', '.', conf.path)
        module = re.sub('\.py$', '', module)
        print("\n\ntesting:%s\n" % module)

        if module == 'test_module':
            pass

        elif module in ['seneca.functional_tester', 'seneca.execute_sc']:
            import functional_tester as ft
            ft.main()

        else:
            print(module)
            m1 = importlib.import_module(module, '..')
            print('* Module loaded.')
            m1.run_tests()
