#!/usr/bin/env python3

import argparse
import importlib
import re
import sys
import os
from os import listdir
from os.path import isfile, join
import glob
import warnings
import configparser
import load_test_conf as lc

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import smart_contract_tester as ft

print('>>>>> Starting test module')


parser = argparse.ArgumentParser()
parser.add_argument("--path", help="Path of the module you want to test.")
conf = parser.parse_args()


def run_tests():
    obj = lambda: None; obj.failed = 0; return obj


def test_py_file(fp):
    print('Loading ' + fp)
    m1 = importlib.import_module(fp, '..')
    print('* Module loaded.')
    return m1.run_tests()

def test_seneca_file(c):
    return ft.run_contract(c)


c_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(c_dir)
os.chdir('..')


def clear_database():
    conn = lc.get_mysql_conn()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute('DROP DATABASE seneca_test;')
    except Exception as e:
        print(e)
    cur.execute('CREATE DATABASE seneca_test;')


def get_relative_path(path):
    return os.path.relpath(path, os.getcwd())


def r_get_by_ext(ext):
    return glob.glob(c_dir + '/**/*.' + ext, recursive=True)


def convert_path_to_module(path):
    mod = re.sub('\/', '.', path)
    return re.sub('\.py$', '', mod)


def test_py_module(path):
    clear_database()
    mod = convert_path_to_module(get_relative_path(path))
    res = test_py_file(mod)
    return res.failed == 0, res


if conf.path:
    f_ext = conf.path.split('.')[-1]

    if f_ext == 'py':
        passed, full_res = test_py_module(conf.path)

        if passed:
            sys.exit(0)
        else:
            print(full_res)
            sys.exit(1)

    elif f_ext == 'seneca':
        clear_database()
        ft.set_up()
        test_seneca_file(conf.path)
    else:
        print('* ERROR: Unknown file type.')
        sys.exit(1)

else:
    for p in r_get_by_ext('py'):
        try:
            test_py_module(p)
        except AttributeError as e:
            print(e)

    # TODO: fix this
    ft.set_up()
    for s in r_get_by_ext('seneca'):
        test_seneca_file(s)



print('... DONE ...')
