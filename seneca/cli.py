import os, seneca, time, redis, subprocess
from os import getenv as env
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter
from seneca.constants.config import get_redis_port, get_redis_password, MASTER_DB, load_env

def cli(fn):
    def _fn(fname, *args, **kwargs):
        si = start_interface()
        print('''
################################################################################
    Operating on "{}"
################################################################################
        '''.format(fname))
        kwargs['scope'] = {
            'rt': {
                'author': kwargs.get('author'),
                'sender': kwargs.get('sender')
            }
        }
        try:
            with open(fname) as f:
                kwargs['fname'] = fname
                fn(si, f.read(), *args, **kwargs)
        except:
            fn(si, fname, *args, **kwargs)
        print('''
################################################################################
    Done.
################################################################################
        ''')
    return _fn

def start_interface():
    start_server()
    SenecaInterpreter.setup()
    return SenecaInterface()

def start_server():
    try:
        conn = redis.StrictRedis(host='localhost', port=get_redis_port(), db=MASTER_DB, password=get_redis_password())
        conn.ping()
    except Exception as ex:
        subprocess.run(['bash', './scripts/start.sh'])
        load_env()


@cli
def run_by_file(si, code_str, *args, **kwargs):
    fname = kwargs.get('fname')
    scope = kwargs.get('scope', {})
    si.execute_code_str(code_str, scope=scope)
    print('"{}" is RUN'.format(fname))

@cli
def publish(si, code_str, fullname, *args, **kwargs):
    scope = kwargs.get('scope', {})
    si.publish_code_str(fullname, code_str, keep_original=True, scope=scope)
    print('"{}" is PUBLISHED'.format(fullname))

@cli
def remove_code(si, fullname, *args, **kwargs):
    si.remove_code(fullname)
    print('"{}" is REMOVED'.format(fullname))

def main():
    import argparse, sys
    parser = argparse.ArgumentParser(description='Run your project on a docker bridge network')
    parser.add_argument('--run', '-r', type=str, help='Run the smart contract file', default=False)
    parser.add_argument('--publish', '-p', type=str, help='Publish the smart contract file')
    parser.add_argument('--name', '-n', type=str, help='Run Name of contract to publish or run')
    parser.add_argument('--author', '-a', type=str, help='Your name as the author of the contract', default="anonnymous_author")
    parser.add_argument('--sender', '-s', type=str, help='Your name as the sender of the contract', default="anonnymous_sender")
    parser.add_argument('--delete', '-d', type=str, help='Smart contract name to delete')
    args = parser.parse_args()

    if args.publish:
        assert args.name, 'Supply the --name option to name the contract you want to publish.'
        publish(args.publish, args.name, author=args.author, sender=args.sender)
    elif args.run:
        if args.run.endswith('.sen.py'):
            run_by_file(args.run, author=args.author, sender=args.sender)
    elif args.delete:
        remove_code(args.delete, author=args.author, sender=args.sender)
    else:
        parser.print_help(sys.stderr)
