from decimal import Decimal as dec

INT_FLAG = b'i'
STR_FLAG = b's'
DEC_FLAG = b'd'
BYT_FLAG = b'b'


def int_to_bytes(i: int):
    return INT_FLAG + str(i).encode()


def str_to_bytes(s: str):
    return STR_FLAG + s.encode()


def decimal_to_bytes(d: dec):
    return DEC_FLAG + str(d).encode()


def bytes_to_bytes(b: bytes):
    return BYT_FLAG + b


type_encoding_map = {
    int: int_to_bytes,
    str: str_to_bytes,
    dec: decimal_to_bytes,
    bytes: bytes_to_bytes
}


def encode(data):
    assert type(data) in type_encoding_map.keys(), 'Unsupported type being passed!'
    return type_encoding_map[type(data)](data)


def decode(data):
    assert type(data) == bytes or data is None, 'Unsupported type being passed!'

    if data is None:
        return data

    t = data[0:1]
    data = data[1:]

    if t == INT_FLAG:
        d = data.decode()
        return int(d)

    elif t == STR_FLAG:
        return data.decode()

    elif t == DEC_FLAG:
        d = data.decode()
        return dec(d)

    elif t == BYT_FLAG:
        return data

    else:
        return None
