balances = Hash(default_value=0)
owners = Hash()
approvals = Hash()

authorized = Hash()

@export
def balance_of(owner):
    assert owner is not None, 'Balance query for the zero address.'
    return balances[owner]

@export
def owner_of(token_id):
    assert token_id is not None, 'Balance query for the zero address'
    return owners[token_id]

@export
def transfer_from(sender, to, token_id):
    # If sender if the caller, pass.
    # If caller is approved, pass.
    # If caller is authorized, pass.
    assert balances[sender] == ctx.caller or \
           approvals[token_id] == ctx.caller or \
           authorized[sender, ctx.caller] is True, 'Access not granted to transfer'

    balances[sender] -= 1
    balances[to] += 1

    owners[token_id] = to

    del approvals[token_id]

@export
def approve(to, token_id):
    assert owners[token_id] == ctx.caller or \
           authorized[sender, ctx.caller] is True, 'Sender is not the owner'

    approvals[token_id] = to

@export
def set_approval_for_all(operator, approved):
    authorized[ctx.caller, operator] = approved

@export
def get_approved(token_id):
    return approvals[token_id]

@export
def is_approved_for_all(owner, operator):
    return authorized[owner, operator]