import erc20
z = erc20.rt
driver = z.env.get('__Driver')

@construct
def seed():
    driver.set(
        key='erc20.balances:stu',
        value=1
    )

@export
def dummy():
    pass
