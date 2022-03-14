import ast as ast39
from typed_ast import ast27
import os
from pychecker.check.common import ast_parse


def parse_import(node):
    names = node.names
    for name in names:
        if name.name != "setuptools":
            continue
        if name.asname:
            return name.asname
        return name.name
    return None


def parse_importfrom(node):
    module = node.module
    if module != "setuptools":
        return None
    for name in node.names:
        if name.name != "setup":
            continue
        if name.asname:
            return name.asname
        return name.name
    return None


def find_setup_candidates(body, this_ast):
    candidates = list()
    for node in body:
        if isinstance(node, this_ast.Import):
            setup_used = parse_import(node)
            if setup_used:
                candidates.append(f"{setup_used}.setup")
        elif isinstance(node, this_ast.ImportFrom):
            setup_used = parse_importfrom(node)
            if setup_used:
                candidates.append(setup_used)
        elif isinstance(node, this_ast.If):
            candidates.extend(find_setup_candidates(node.body, this_ast))
            candidates.extend(find_setup_candidates(node.orelse, this_ast))
        elif isinstance(node, ast39.Try) or isinstance(node, ast27.TryExcept):
            candidates.extend(find_setup_candidates(node.body, this_ast))
            candidates.extend(find_setup_candidates(node.orelse, this_ast))
            # candidates.extend(find_setup_candidates(node.finalbody, this_ast))
            for handler in node.handlers:
                candidates.extend(find_setup_candidates(handler.body, this_ast))
    return candidates


def get_func(node, this_ast):
    if isinstance(node, this_ast.Attribute):
        attr = node.attr
        name = get_func(node.value, this_ast)
        func = f"{name}.{attr}"
        return func
    if isinstance(node, this_ast.Name):
        return node.id
    return None


def is_setup_call(expr, candidates, this_ast):
    if isinstance(expr, this_ast.Attribute) or isinstance(expr, this_ast.Name):
        func_name = get_func(expr, this_ast)
        if func_name in candidates:
            return True
    return False


def find_setup_params_expr(expr, candidates, this_ast):
    setup_param = None
    if isinstance(expr, this_ast.Call) and is_setup_call(expr.func, candidates, this_ast):
        setup_param = expr.keywords

    return setup_param


def find_setup_params(body, candidates, this_ast):
    setup_param = None
    for node in body:
        if isinstance(node, this_ast.If):
            setup_param = find_setup_params(node.body, candidates, this_ast)
        elif isinstance(node, this_ast.Expr):
            setup_param = find_setup_params_expr(node.value, candidates, this_ast)
        elif isinstance(node, this_ast.FunctionDef):
            setup_param = find_setup_params(node.body, candidates, this_ast)

        if setup_param:
            return setup_param
    return None


def analysis_setup_python_requires(code):
    # root = ast.parse(code)
    body, this_ast = ast_parse(code)

    candidates = find_setup_candidates(body, this_ast)
    if not candidates:
        return False

    setup_params = find_setup_params(body, candidates, this_ast)
    if not setup_params:
        return False

    for param in setup_params:
        if not param.arg:
            pass
        if param.arg == "python_requires":
            return True
    return False
