balances = Hash(default_value=0)
owners = Hash()
approvals = Hash()
authorized = Hash()
controllers = Hash()

@seed
def construct(vk):
    controllers[vk] = True

@export
def add_controller(vk):
    assert controllers[ctx.caller]
    controllers[vk] = True

@export
def revoke_controller(vk):
    assert controllers[ctx.caller]
    controllers[vk] = False

@export
def mint(token_id):
    assert controllers[ctx.caller]
    assert owners[token_id] is None, 'Already issued!'

    owners[token_id] = ctx.caller
    balances[ctx.caller] += 1

@export
def burn(token_id):
    assert balances[sender] == ctx.caller or \
           approvals[token_id] == ctx.caller or \
           authorized[sender, ctx.caller] is True, 'Access not granted to transfer'

    balances[sender] -= 1
    owners[token_id] = None

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
    assert balances[sender] == ctx.caller or \
           approvals[token_id] == ctx.caller or \
           authorized[sender, ctx.caller] is True, 'Access not granted to transfer'
    balances[sender] -= 1
    balances[to] += 1
    owners[token_id] = to

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
