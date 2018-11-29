import importlib


def import_contract(n):
    print('assert this sucker is in the state')

    contract = importlib.import_module(n)
