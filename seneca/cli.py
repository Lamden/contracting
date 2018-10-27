import os, seneca
from os import getenv as env
from seneca.interface.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter

def cli(fn):
    def _fn(si, fname, *args, **kwargs):
        print('''
################################################################################
    Running "{}"
################################################################################
        '''.format(fname))
        with open(fname) as f:
            fn(si, f.read(), *args, **kwargs)
        print('''
################################################################################
    Done.
################################################################################
        ''')
    return _fn

def start_interface():
    SenecaInterpreter.setup()
    return SenecaInterface()

@cli
def run(si, code_str):
    si.execute_code_str(code_str, scope={})

@cli
def publish(si, code_str, fullname):
    si.publish_code_str(fullname, code_str, keep_original=True, scope={})

def main():
    import argparse, sys
    parser = argparse.ArgumentParser(description='Run your project on a docker bridge network')
    parser.add_argument('--run', '-r', type=str, help='Run the smart contract file', default=True)
    parser.add_argument('--publish', '-p', type=str, help='Publish the smart contract file')
    parser.add_argument('--name', '-n', type=str, help='Run Name of contract to publish or run')
    parser.add_argument('--author', '-a', type=str, help='Your name as the author of the contract', default="anonnymous_author")
    parser.add_argument('--sender', '-s', type=str, help='Your name as the sender of the contract', default="anonnymous_sender")
    args = parser.parse_args()

    if args.publish and args.name:
        publish(start_interface(), args.publish, args.name)
    elif args.run and args.name:
        run_by_name(start_interface(), args.name)
    elif args.run != True:
        run(start_interface(), args.run)
    else:
        parser.print_help(sys.stderr)
