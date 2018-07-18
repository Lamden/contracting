import ast

permitted_ast_types = {
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
        ast.ExceptHandler,
        ast.Try,
        # comprehension
        ast.ListComp,
        ast.comprehension,
        ast.Slice,
        ast.USub,
        # Conditonals
        ast.BoolOp,
        ast.And,
        ast.Or
    }

def validate(a):
    # Basic whitelist validation
    current_ast_types = {type(x) for x in ast.walk(a)}

    illegal_ast_nodes = current_ast_types - permitted_ast_types

    wl_error_message = 'Found illegal AST node(s) in module: ' + ', '.join(
      map(str, illegal_ast_nodes)
    )

    assert not illegal_ast_nodes, wl_error_message


def run_tests():
    '''
    >>> validate(ast.parse('import some_sc').body[0])
    >>> try:
    ...     validate(ast.parse('for x in []: pass').body[0])
    ... except Exception as e:
    ...     print(e)
    Found illegal AST node(s) in module: <class '_ast.For'>

    '''
    import doctest, sys, ast
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
