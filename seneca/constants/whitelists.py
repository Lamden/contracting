import ast, builtins

ALLOWED_AST_TYPES = {
    ast.Module,
    ast.Eq,
    ast.Call,
    ast.Dict,
    ast.Attribute,
    ast.Pow,
    ast.Index,
    ast.Not,
    ast.alias,
    ast.If,
    ast.FunctionDef,
    ast.GtE,
    ast.LtE,
    ast.Load,
    ast.arg,
    ast.Add,
    ast.Lambda,
    ast.Import,
    ast.ImportFrom,
    ast.Name,
    ast.Num,
    ast.BinOp,
    ast.Store,
    ast.Assert,
    ast.Assign,
    ast.AugAssign,
    ast.Subscript,
    ast.Compare,
    ast.Return,
    ast.NameConstant,
    ast.Expr,
    ast.keyword,
    ast.Sub,
    ast.arguments,
    ast.List,
    ast.Set,
    ast.Str,
    ast.UnaryOp,
    ast.Pass,
    ast.Tuple,
    ast.Div,
    ast.In,
    ast.NotIn,
    ast.Gt,
    ast.Lt,
    ast.Starred,
    ast.Mod,
    ast.NotEq,
    # TODO: Decide if we actually want these
    # Error handling
    # ast.ExceptHandler,
    # ast.Try,
    # Loops
    ast.For,
    ast.While,
    # comprehension
    ast.ListComp,
    ast.comprehension,
    ast.Slice,
    ast.USub,
    # Conditonals
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.Mult,
}

SENECA_LIBRARY_PATH = 'seneca.libs'

ALLOWED_IMPORT_PATHS = [
    'seneca.contracts',
    'test_contracts'
]

_SAFE_NAMES = [
    '__import__',

    'None',
    'False',
    'True',

    'callable',
    'isinstance',
    'issubclass',

    'abs',
    'bool',
    'chr',
    'complex',
    'divmod',
    'float',
    'hash',
    'hex',
    'id',
    'int',

    'len',
    'oct',
    'ord',
    'pow',
    'range',
    'repr',
    'round',
    'slice',
    'str',
    'tuple',
    'zip',

    # JUST FOR TESTING! TODO remove this irl
    'dir',
    'help',
    'print',
    # 'globals'
]

_SAFE_EXCEPTIONS = [
    'ArithmeticError',
    'AssertionError',
    'AttributeError',
    'BaseException',
    'BufferError',
    'BytesWarning',
    'DeprecationWarning',
    'EOFError',
    'EnvironmentError',
    'Exception',
    'FloatingPointError',
    'FutureWarning',
    'GeneratorExit',
    'IOError',
    'ImportError',
    'ImportWarning',
    'IndentationError',
    'IndexError',
    'KeyError',
    'KeyboardInterrupt',
    'LookupError',
    'MemoryError',
    'NameError',
    'NotImplementedError',
    'OSError',
    'OverflowError',
    'PendingDeprecationWarning',
    'ReferenceError',
    'RuntimeError',
    'RuntimeWarning',
    'StopIteration',
    'SyntaxError',
    'SyntaxWarning',
    'SystemError',
    'SystemExit',
    'TabError',
    'TypeError',
    'UnboundLocalError',
    'UnicodeDecodeError',
    'UnicodeEncodeError',
    'UnicodeError',
    'UnicodeTranslateError',
    'UnicodeWarning',
    'UserWarning',
    'ValueError',
    'Warning',
    'ZeroDivisionError',
]

SAFE_BUILTINS = {}

for name in _SAFE_NAMES:
    SAFE_BUILTINS[name] = getattr(builtins, name)

for name in _SAFE_EXCEPTIONS:
    SAFE_BUILTINS[name] = getattr(builtins, name)
