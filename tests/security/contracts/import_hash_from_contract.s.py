import erc20

@construct
def seed():
    erc20.balances['stu'] = 999999999999

@export
def dummy():
    return 0