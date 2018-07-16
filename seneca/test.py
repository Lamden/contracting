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
import MySQLdb

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import functional_tester as ft

print('>>>>> Starting test module')


parser = argparse.ArgumentParser()
parser.add_argument("--path", help="Path of the module you want to test.")
conf = parser.parse_args()


def run_tests():
    # Intentionally left blank, this file doesn't have any tests.
    pass


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
    settings = configparser.ConfigParser()
    settings._interpolation = configparser.ExtendedInterpolation()
    settings.read(os.path.join('seneca/seneca_internal/storage/', 'test_db_conf.ini'))
    conn = MySQLdb.connect(host=settings.get('DB', 'hostname'),
                       user=settings.get('DB', 'username'),
                       passwd=settings.get('DB', 'password'),
                       port=3306,
                       connect_timeout=5)
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
    test_py_file(mod)


if conf.path:
    test_py_module(conf.path)
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
