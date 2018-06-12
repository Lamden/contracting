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
        ast.ExceptHandler,
        ast.Try,
    }

def validate(a):
    # Basic whitelist validation
    current_ast_types = {type(x) for x in ast.walk(a)}

    illegal_ast_nodes = current_ast_types - permitted_ast_types

    wl_error_message = 'Found illegal AST node(s) in module: ' + ', '.join(
      map(str, illegal_ast_nodes)
    )

    assert not illegal_ast_nodes, wl_error_message
