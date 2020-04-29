@__export('submission')
def submit_contract(name: str, code: str, owner: Any=None, constructor_args: dict={}):
    __Contract().submit(name=name, code=code, owner=owner, constructor_args=constructor_args)
