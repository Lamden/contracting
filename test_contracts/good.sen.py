balances = {'hello': 'world'}

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
