#!/usr/bin/env python3

import argparse
import importlib
import re

# This utility exists to deal with relative imports

parser = argparse.ArgumentParser()
parser.add_argument("--path", help="Path of the module you want to test.")
conf = parser.parse_args()


if hasattr(conf, 'path'):
    if conf.path == __file__:
        pass
    else:
        module = re.sub('\/', '.', conf.path)
        module = re.sub('\.py$', '', module)
        print("\n\ntesting:%s\n" % module)

        if module == 'test_module':
            pass

        elif module in ['functional_tester', 'execute_sc']:
            import functional_tester as ft
            ft.main()

        else:
            m1 = importlib.import_module(module)
            m1.run_tests()
