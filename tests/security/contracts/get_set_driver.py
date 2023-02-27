import erc20
driver = erc20.rt.env.get('__Driver')

@construct
def seed():
    driver.set(
        key='erc20.balances:stu',
        value=1
    )

@export
def dummy():
    pass
