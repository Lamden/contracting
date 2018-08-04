#!/usr/bin/env python3

# TODO: pass on modules that don't have a run_tests function
# TODO: Raise test coverage requirement in Makefile

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
from typing import Tuple
from engine.util import auto_set_fields

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import smart_contract_tester as ft

from seneca.engine.storage.mysql_executer import Executer as Raw_Executer
from seneca.engine.storage.mysql_spits_executer import Executer as Spits_Executer

clean_up_actions = []


def clear_database():
    conn = lc.get_mysql_conn()
    conn.autocommit = False
    cur = conn.cursor()
    try:
        cur.execute('DROP DATABASE seneca_test;')
    except Exception as e:
        print(e)
    cur.execute('CREATE DATABASE seneca_test;')


def deps_provider(some_type):
    if some_type == Raw_Executer:
        rex = Raw_Executer(**lc.db_settings)
        clean_up_actions.append(lambda: rex.kill())
        return rex
    elif some_type == Spits_Executer:
        spex = Spits_Executer(**lc.db_settings)
        clean_up_actions.append(lambda: spex.kill())
        return spex
    elif some_type == Tuple[Spits_Executer, Raw_Executer]:
        spex = Spits_Executer(**lc.db_settings)
        bex = Raw_Executer(**lc.db_settings)

        bex.conn = spex.conn
        bex.cur = spex.cur
        clean_up_actions.append(lambda: spex.kill())

        return spex,bex

    else:
        raise Exception('Requested type not found!!!')


def clean_up():
    while clean_up_actions:
        clean_up_actions.pop()()


def test_seneca_file(path):
    try:
        ft.set_up()
        # TODO: Real Seneca testing functionality
        ft.run_contract(path)
        return TestOutcome(path, None, None, None)
    finally:
        ft.clean_up()


def get_relative_path(path):
    return os.path.relpath(path, os.getcwd())


def r_get_by_ext(ext):
    return glob.glob(c_dir + '/**/*.' + ext, recursive=True)


def convert_path_to_module(path):
    mod = re.sub('\/', '.', path)
    return re.sub('\.py$', '', mod)


class TestOutcome(object):
    @auto_set_fields
    def __init__(self, path, ran_successfully, attempted, failed):
        pass

    def summarize(self):
        s_d = self.__dict__
        if self.ran_successfully is None:
            return '* Skipped: {path}, no tests.'.format(**s_d)
        elif self.ran_successfully == False:
            return '* Failed: {path}, attempted: {attempted}, failed: {failed}.'.format(**s_d)
        elif self.ran_successfully == True:
            return '* Passed {path}, passed: {attempted}'.format(**s_d)

def test_py_module(path):
    try:
        mod = convert_path_to_module(get_relative_path(path))
        clear_database()
        #print('* Loading module' + path + '... ', end='', flush=True)
        m1 = importlib.import_module(mod, '..')
        #print('Done.')
        if hasattr(m1, 'run_tests'):
            res = m1.run_tests(deps_provider)
            return TestOutcome(path, res.failed == 0, res.attempted, res.failed)
        else:
            return TestOutcome(path, None, None, None)
    finally:
        clean_up()


def get_file_extension(path):
    return path.split('.')[-1]


def test_file(path):
    ext = get_file_extension(path)

    if ext == 'py':
        return test_py_module(path)
    elif ext == 'seneca':
        return test_seneca_file(path)
    else:
        print('* ERROR: Unknown file type.', file=sys.stderr)
        sys.exit(1)


def overall_summary(res):
    successful = [x for x in res if x.ran_successfully == True]
    failed = [x for x in res if x.ran_successfully == False]
    skipped = [x for x in res if x.ran_successfully is None]

    successful_file_count = len(successful)
    failed_file_count = len(failed)
    skipped_file_count = len(skipped)

    failed_test_count = sum([x.failed for x in res if x.failed is not None])
    successful_test_count = sum(x.attempted for x in res if x.attempted is not None) - failed_test_count

    skipped_file_list = '\n\t'.join([x.path for x in skipped]) if skipped else '<none>'
    failed_file_list = '\n\t'.join([x.path for x in failed]) if failed else '<none>'

    return '''
Stats:

    Skipped file names:
        {skipped_file_list}

    Failed file names:
        {failed_file_list}

    File-level metrics:
        Passed: {successful_file_count}, Failed: {failed_file_count}, Skipped: {skipped_file_count}

    Test-level metrics:
        Passed: {successful_test_count}, Failed: {failed_test_count}
    '''.format(**locals())


if __name__ == '__main__':
    import load_test_conf as lc
    print('\n*** Running Tests ***', file=sys.stderr)

    c_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(c_dir)
    os.chdir('..')

    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="Path of the module you want to test.")
    conf = parser.parse_args()

    results = []

    if conf.path:
        res = test_file(conf.path)
        results.append(res)
        print('\t' + res.summarize(), file=sys.stderr)

    else:
        python_files = r_get_by_ext('py')
        seneca_files = r_get_by_ext('seneca')

        print('\nTesting Python files...', file=sys.stderr)
        for f in python_files:
            res = test_file(f)
            results.append(res)
            print('\t' + res.summarize(), file=sys.stderr)

        print('\nTesting Seneca files...', file=sys.stderr)
        for f in seneca_files:
            res = test_file(f)
            results.append(res)
            print('\t' + res.summarize(), file=sys.stderr)

        print(overall_summary(results))
    failed_tests = sum([x.failed for x in results if x.failed is not None])

    if failed_tests > 0:
        print('*** Failed ***', file=sys.stderr)
        sys.exit(1)
    else:
        print('*** Testing Complete ***', file=sys.stderr)
        sys.exit(0)
