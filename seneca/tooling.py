import autopep8
import inspect
from .execution.executor import Executor


def function_to_code_string(f):
    _code = inspect.getsourcelines(f)[0]
    _code = _code[1:]
    code_str = ''
    for c in _code:
        code_str += c

    standard_indented_code = autopep8.fix_code(code_str, options={'select': ['E101']})

    final_code = ''
    for line in standard_indented_code.split('\n'):
        if line.startswith('    '):
            final_code += line[4:] + '\n'

    final_code = autopep8.fix_code(final_code)

    return final_code


def publish(f, contract_name, author):
    code_str = function_to_code_string(f)
