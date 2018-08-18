'''
Some code for GetExactType, or better, use Lua

if issubclass(existing_type, desired_type):
    return True
elif existing_type == RScalar and issubclass(desired_type, RScalar):
    # Now we have to find the Redis inferred internal type.
    if desired_type in [ScalarRaw, ScalarString]:
        return True
    elif desired_type == ScalarInt:
        try
    elif desired_type == ScalarFloat:
        pass
    else:
        pass
else:
    raise Exception('Unknown type.')


TODO, implement:
* Get
* Set
* Incr
* IncrBy
* Decr
* DecrBy

* Exists
* Type
* GetExactType

*




'''
from seneca.engine.storage.resp_commands import *
