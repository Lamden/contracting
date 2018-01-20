### A brain dump so I don't forget.

```
new table 'users' 
	(text userid,
	text first_name,
	text last_name)

delete user from table
	where user.name = (name)
	if user.timestamp == 12345

insert (object) into users
	if not exists...

delete (variable) from table
	where (variable).name = (name)
	if (variable).timestamp == (time)


delete(text user):
	user = select (user) from table
	assert user.owner == sender
	delete (user) from table


maximum stack size = 32
prevent recursion though blocking boolean flags?

import all from friend/token

contract Token:
	text something

	new public table 'users' 
		(text userid,
		text first_name,
		text last_name)

	new private table 'balances'
		(text userid,
		text first_name,
		text last_name)

	new private keyset 'keys'

	new public table 'keys'
		(text public_key)

	method():
		access control (which are statments)
		statement

	_internal():
		log('something fun here that gets returned to the sender!')

insert {
	balance : balance,
	'blah' : user_info
}
```

A contract starts like a Python class. From there, the constructor / initializer is from the point of contract declaration to the first method. It's probably best that there are no constructor arguments for the time being because that introduces a level of complexity that we should not worry about until a testing infrastructure is up.

That being said, you can easily define public/private resources. If something is public, it means that someone can access it from another contract or from the regular API. It does not mean that they can interface with it. Only the public getter and setter function in the original smart contract can interact with datatables.

After that, methods are created much like Python methods in such that each one has a name and a set of **STRONGLY TYPED** variables. Indentation notation (ha) is nice and neat, so let's use it.

The _ modifier could be used as well to determine if a method is public or private. However, this would be confusing if you are using `public / private` for constructor variables but not methods so we should fixate on a single one.

Simple math needs to be added.

**GET THIS.** Seneca supports fixed precision decimals like a normal goddamn language. I don't know why Solidity makes it so hard for you to do this, but as a result the entire token economy runs on big endian integers where 1 actually is 1,000,000,000,000,000,000 and then obstructed from the average user on the front end. Why? I don't know...

#### Things to think about

Recursion will destroy this smart contracting language. It will destroy really any smart contracting language. So, we have to figure out a simple solution by which a stack-depth maximum is introduced and we identify circular dependencies immediately.

Right now, the best thing to do would be to keep the system synchronous and then block interaction with a smart contract if its already being interacted with in the stack so that ciruclar dependecies and extra-contractual recursion can't exist.
