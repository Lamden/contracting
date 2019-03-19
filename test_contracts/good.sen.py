from seneca.libs.storage.datatypes import Hash

balances = Hash('hello')

@export
def one_you_can_export():
    print('Running one_you_can_export()')

@export
def one_you_can_also_export():
    print('Running one_you_can_also_export()')
    one_you_can_export()


def one_you_cannot_export(dont, do, it='wrong'):
    print('Always runs: Running one_you_cannot_export()')

@export
def one_you_can_also_also_export():
    print('Running one_you_can_also_also_export()')
    one_you_cannot_export('a', 'b', it='c')

@export
def assert_export_to_sample():
    assert rt['contract'] == 'good' and rt['sender'] == 'sample', 'Not inheirting sender properly'