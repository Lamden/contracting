@seneca_export
def submit_contract(name, code):
    author = ctx.signer
    Contract().submit(name=name, code=code, author=author)
