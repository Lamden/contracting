import json
import decimal
from ..stdlib.bridge.time import Datetime

##
# ENCODER CLASS
# Add to this to encode Python types for storage.
# Right now, this is only for datetime types. They are passed into the system as ISO strings, cast into Datetime objs
# and stored as dicts. Is there a better way? I don't know, maybe.
##


class Encoder(json.JSONEncoder):
    def default(self, o, *args):
        if isinstance(o, Datetime):
            return {
                '__time__': [o.year, o.month, o.day, o.hour, o.minute, o.second, o.microsecond]
            }
        if isinstance(o, bytes):
            return o.hex()
        return super().default(o)


# JSON library from Python 3 doesn't let you instantiate your custom Encoder. You have to pass it as an obj to json
def encode(data: str):
    return json.dumps(data, cls=Encoder)


def as_object(d):
    if '__time__' in d:
        return Datetime(*d['__time__'])
    return dict(d)


# Decode has a hook for JSON objects, which are just Python dictionaries. You have to specify the logic in this hook.
# This is not uniform, but this is how Python made it.
def decode(data):
    if data is None:
        return None

    if isinstance(data, bytes):
        data = data.decode()

    try:
        return json.loads(data, parse_float=decimal.Decimal, object_hook=as_object)
    except json.decoder.JSONDecodeError as e:
        return None
