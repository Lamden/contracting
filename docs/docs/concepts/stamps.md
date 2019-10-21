## Stamps

A stamp is a single unit of computational work in a smart contract. Stamps are converted from cryptocurrency on the main Lamden network. This is what enforces rate limiting and incentivizes the development of the network.

To calculate work, the code is ran through an optimized tracer. Each Python VM opcode has a specific cost. Each step of the code deducts from the number of stamps attached to the transaction.

If all of the stamps are deducted before the transaction is done, the transaction reverts states and fails. If there are left over stamps from the transaction execution, they are returned to the sender.

## Read Write Costs
* Cost to read one byte from state: 3 stamps
* Cost to write one byte to state: 25 stamps

## Opcode Cost Chart

Details on Python Opcodes from the `dis` module documentation [here](https://docs.python.org/3/library/dis.html). CPython Opcode definitions [here](https://github.com/python/cpython/blob/master/Include/opcode.h).

Some opcodes that are never encountered due to the linter failing the contract on submission have been left out of this table. Inversely, not all opcodes in this list may ever be encountered in valid Contracting code.

| Op Code                      | Num | Cost | Muliplier | Actual Cost |
|------------------------------|-----|------|-----------|-------------|
| POP_TOP                      | 1   | 1    | 2         | 2           |
| ROT_TWO                      | 2   | 2    | 2         | 4           |
| ROT_THREE                    | 3   | 2.5  | 2         | 5           |
| DUP_TOP                      | 4   | 1    | 2         | 2           |
| DUP_TOP_TWO                  | 5   | 2    | 2         | 4           |
| NOP                          | 9   | 1    | 2         | 2           |
| UNARY_POSITIVE               | 10  | 1    | 2         | 2           |
| UNARY_NEGATIVE               | 11  | 1.5  | 2         | 3           |
| UNARY_NOT                    | 12  | 1    | 2         | 2           |
| UNARY_INVERT                 | 15  | 2    | 2         | 4           |
| BINARY_POWER                 | 19  | 15   | 2         | 30          |
| BINARY_MULTIPLY              | 20  | 1.5  | 2         | 3           |
| BINARY_MODULO                | 22  | 2    | 2         | 4           |
| BINARY_ADD                   | 23  | 1.5  | 2         | 3           |
| BINARY_SUBTRACT              | 24  | 1.5  | 2         | 3           |
| BINARY_SUBSCR                | 25  | 1.5  | 2         | 3           |
| BINARY_FLOOR_DIVIDE          | 26  | 2    | 2         | 4           |
| BINARY_TRUE_DIVIDE           | 27  | 2    | 2         | 4           |
| INPLACE_FLOOR_DIVIDE         | 28  | 2    | 2         | 4           |
| INPLACE_TRUE_DIVIDE          | 29  | 2.5  | 2         | 5           |
| INPLACE_ADD                  | 55  | 2.5  | 2         | 5           |
| INPLACE_SUBTRACT             | 56  | 2.5  | 2         | 5           |
| INPLACE_MULTIPLY             | 57  | 2    | 2         | 4           |
| INPLACE_MODULO               | 59  | 2    | 2         | 4           |
| STORE_SUBSCR                 | 60  | 2    | 2         | 4           |
| DELETE_SUBSCR                | 61  | 2    | 2         | 4           |
| BINARY_LSHIFT                | 62  | 3    | 2         | 6           |
| BINARY_RSHIFT                | 63  | 3    | 2         | 6           |
| BINARY_AND                   | 64  | 3    | 2         | 6           |
| BINARY_XOR                   | 65  | 3    | 2         | 6           |
| BINARY_OR                    | 66  | 3    | 2         | 6           |
| INPLACE_POWER                | 67  | 15   | 2         | 30          |
| GET_ITER                     | 68  | 3.5  | 2         | 7           |
| GET_YIELD_FROM_ITER          | 69  | 6    | 2         | 12          |
| LOAD_BUILD_CLASS             | 71  | 805  | 2         | 1610        |
| INPLACE_LSHIFT               | 75  | 3    | 2         | 6           |
| INPLACE_RSHIFT               | 76  | 3    | 2         | 6           |
| INPLACE_AND                  | 77  | 3    | 2         | 6           |
| INPLACE_XOR                  | 78  | 3    | 2         | 6           |
| INPLACE_OR                   | 79  | 3    | 2         | 6           |
| BREAK_LOOP                   | 80  | 1    | 2         | 2           |
| WITH_CLEANUP_START           | 81  | 7.5  | 2         | 15          |
| WITH_CLEANUP_FINISH          | 82  | 7.5  | 2         | 15          |
| RETURN_VALUE                 | 83  | 1    | 2         | 2           |
| IMPORT_STAR                  | 84  | 63   | 2         | 126         |
| SETUP_ANNOTATIONS            | 85  | 500  | 2         | 1000        |
| POP_BLOCK                    | 87  | 2    | 2         | 4           |
| END_FINALLY                  | 88  | 2    | 2         | 4           |
| POP_EXCEPT                   | 89  | 2    | 2         | 4           |
| STORE_NAME                   | 90  | 1    | 2         | 2           |
| DELETE_NAME                  | 91  | 1    | 2         | 2           |
| UNPACK_SEQUENCE              | 92  | 4    | 2         | 8           |
| FOR_ITER                     | 93  | 4    | 2         | 8           |
| UNPACK_EX                    | 94  | 1    | 2         | 2           |
| STORE_ATTR                   | 95  | 3    | 2         | 6           |
| DELETE_ATTR                  | 96  | 3    | 2         | 6           |
| STORE_GLOBAL                 | 97  | 2    | 2         | 4           |
| DELETE_GLOBAL                | 98  | 2    | 2         | 4           |
| LOAD_CONST                   | 100 | 1    | 2         | 2           |
| LOAD_NAME                    | 101 | 1    | 2         | 2           |
| BUILD_TUPLE                  | 102 | 1    | 2         | 2           |
| BUILD_LIST                   | 103 | 2.5  | 2         | 5           |
| BUILD_SET                    | 104 | 4    | 2         | 8           |
| BUILD_MAP                    | 105 | 3.5  | 2         | 7           |
| LOAD_ATTR                    | 106 | 2    | 2         | 4           |
| COMPARE_OP                   | 107 | 2    | 2         | 4           |
| IMPORT_NAME                  | 108 | 19   | 2         | 38          |
| IMPORT_FROM                  | 109 | 63   | 2         | 126         |
| JUMP_FORWARD                 | 110 | 2    | 2         | 4           |
| JUMP_IF_FALSE_OR_POP         | 111 | 2    | 2         | 4           |
| JUMP_IF_TRUE_OR_POP          | 112 | 2    | 2         | 4           |
| JUMP_ABSOLUTE                | 113 | 2    | 2         | 4           |
| POP_JUMP_IF_FALSE            | 114 | 2    | 2         | 4           |
| POP_JUMP_IF_TRUE             | 115 | 2    | 2         | 4           |
| LOAD_GLOBAL                  | 116 | 1.5  | 2         | 3           |
| CONTINUE_LOOP                | 119 | 1    | 2         | 2           |
| SETUP_LOOP                   | 120 | 2    | 2         | 4           |
| SETUP_EXCEPT                 | 121 | 1    | 2         | 2           |
| SETUP_FINALLY                | 122 | 1.5  | 2         | 3           |
| LOAD_FAST                    | 124 | 1    | 2         | 2           |
| STORE_FAST                   | 125 | 1    | 2         | 2           |
| DELETE_FAST                  | 126 | 1    | 2         | 2           |
| STORE_ANNOTATION             | 127 | 500  | 2         | 1000        |
| RAISE_VARARGS                | 130 | 2.5  | 2         | 5           |
| CALL_FUNCTION                | 131 | 4.5  | 2         | 9           |
| MAKE_FUNCTION                | 132 | 3.5  | 2         | 7           |
| BUILD_SLICE                  | 133 | 6    | 2         | 12          |
| LOAD_CLOSURE                 | 135 | 3.5  | 2         | 7           |
| LOAD_DEREF                   | 136 | 1    | 2         | 2           |
| STORE_DEREF                  | 137 | 1    | 2         | 2           |
| DELETE_DEREF                 | 138 | 1    | 2         | 2           |
| CALL_FUNCTION_KW             | 141 | 6    | 2         | 12          |
| CALL_FUNCTION_EX             | 142 | 6    | 2         | 12          |
| SETUP_WITH                   | 143 | 7.5  | 2         | 15          |
| LIST_APPEND                  | 145 | 4    | 2         | 8           |
| SET_ADD                      | 146 | 4    | 2         | 8           |
| MAP_ADD                      | 147 | 2.5  | 2         | 5           |
| LOAD_CLASSDEREF              | 148 | 1    | 2         | 2           |
| EXTENDED_ARG                 | 144 | 1    | 2         | 2           |
| BUILD_LIST_UNPACK            | 149 | 2.5  | 2         | 5           |
| BUILD_MAP_UNPACK             | 150 | 3.5  | 2         | 7           |
| BUILD_MAP_UNPACK_WITH_CALL   | 151 | 4.5  | 2         | 9           |
| BUILD_TUPLE_UNPACK           | 152 | 1    | 2         | 2           |
| BUILD_SET_UNPACK             | 153 | 4    | 2         | 8           |
| FORMAT_VALUE                 | 155 | 15   | 2         | 30          |
| BUILD_CONST_KEY_MAP          | 156 | 3.5  | 2         | 7           |
| BUILD_STRING                 | 157 | 4    | 2         | 8           |
| BUILD_TUPLE_UNPACK_WITH_CALL | 158 | 2    | 2         | 4           |