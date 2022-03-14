import os
import re
import pychecker.config as config
from pychecker.utils import read_object_from_file
from pychecker.check.common import analysis, ast_parse
from pychecker.check.Parser import ParserFactory
import ast as ast39
from typed_ast import ast27


def reverse_std_modules(std_modules):
    new_dict = dict()
    for pyver, modules in std_modules.items():
        for module in modules:
            if module not in new_dict:
                new_dict[module] = list()
            new_dict[module].append(pyver)
    return new_dict


std_modules = read_object_from_file(os.path.join(config.CACHE_DIR, "standard_top_level.json"))
std_modules = reverse_std_modules(std_modules)
syntax_features = read_object_from_file(os.path.join(config.CACHE_DIR, "python_features.json"))


def use_incomp_feature(path, **kwargs):
    comp_info = kwargs['comp_info'] if 'comp_info' in kwargs else config.PY_VERSIONS
    custom_modules = kwargs['custom_modules'] if 'custom_modules' in kwargs else set()
    top_levels = extract_top_levels(path)
    top_levels -= custom_modules
    features = extract_feature(path)
    comp_python = find_comp_pyvers(top_levels, features)
    if use_open_encoding_kwarg(path):
        comp_python -= {"2.7"}
    difference = set(comp_info)-set(comp_python)
    if len(difference):
        return True
    return False


def detect_incomp_feature_usage(path, comp_info, local_modules):
    return analysis(path, use_incomp_feature, comp_info=comp_info, custom_modules=local_modules)


def extract_feature(path):
    matched_features = set()

    file = open(path)
    lines = file.readlines()
    file.close()
    for line in lines:
        if line.startswith("#"):
            continue
        for feature in syntax_features.keys():
            line = line.strip()
            if feature in matched_features:
                continue
            pattern = re.compile(syntax_features[feature]["regex"])
            if pattern.match(line):
                # print(feature.regex)
                # print(line)
                matched_features.add(feature)
                break
    return matched_features


def extract_top_levels(path):
    # TODO: unify ast parse
    parser = ParserFactory.make_parser("top_level")
    with open(path) as f:
        lines = f.readlines()
        code = "".join(lines)
        top_levels = parser.parse_modules(code)

    return top_levels


def find_comp_pyvers(modules, features):
    comp_pyvers = set(config.PY_VERSIONS)
    for module in modules:
        if module not in std_modules:
            continue
        comp_pyvers = comp_pyvers.intersection(std_modules[module])

    for feature in features:
        comp_pyvers = comp_pyvers.intersection(syntax_features[feature]["pyver"])
    return comp_pyvers

# def use_open_encoding_kwarg(path):
#     pattern = re.compile(r".*open\(.*,\s*encoding\s*=.*")
#     # pattern_io = re.compile(r".*io\.open\(.*,\s*encoding\s*=.*")
#     lines = open(path).readlines()
#     for line in lines:
#         if pattern.match(line) and "io.open" not in line and "codecs.open" not in line:
#             return True
#     return False


# TODO: refactor open-encoding and setup-python_requires
def parse_import(node):
    names = node.names
    for name in names:
        if name.name != "io" and name.name != "codecs":
            continue
        if name.asname:
            return name.asname
        return name.name
    return None


def parse_importfrom(node):
    module = node.module
    if module != "io" and module != "codecs":
        return None
    for name in node.names:
        if name.name != "open":
            continue
        if name.asname:
            return name.asname
        return name.name
    return None


def find_open_candidates(body, this_ast):
    candidates = list()
    for node in body:
        if isinstance(node, this_ast.Import):
            setup_used = parse_import(node)
            if setup_used:
                candidates.append(f"{setup_used}.open")
        elif isinstance(node, this_ast.ImportFrom):
            setup_used = parse_importfrom(node)
            if setup_used:
                candidates.append(setup_used)
        elif isinstance(node, this_ast.If):
            candidates.extend(find_open_candidates(node.body, this_ast))
            candidates.extend(find_open_candidates(node.orelse, this_ast))
        elif isinstance(node, ast39.Try) or isinstance(node, ast27.TryExcept):
            candidates.extend(find_open_candidates(node.body, this_ast))
            candidates.extend(find_open_candidates(node.orelse, this_ast))
            # candidates.extend(find_setup_candidates(node.finalbody, this_ast))
            for handler in node.handlers:
                candidates.extend(find_open_candidates(handler.body, this_ast))
    return candidates


def find_open_params(body, candidates, this_ast):
    open_params = None
    for node in body:
        if isinstance(node, this_ast.If):
            open_params = find_open_params(node.body, candidates, this_ast)
            if not open_params:
                open_params = find_open_params(node.orelse, candidates, this_ast)
        elif isinstance(node, this_ast.Expr):
            open_params = find_open_params_expr(node.value, candidates, this_ast)
        elif isinstance(node, this_ast.FunctionDef):
            open_params = find_open_params(node.body, candidates, this_ast)
        elif isinstance(node, this_ast.Assign):
            open_params = find_open_params_expr(node.value, candidates, this_ast)
        elif isinstance(node, this_ast.Return):
            open_params = find_open_params_expr(node.value, candidates, this_ast)
        elif isinstance(node, ast39.Try) or isinstance(node, ast27.TryExcept):
            open_params = find_open_params(node.body, candidates, this_ast)
            if not open_params:
                open_params = find_open_params(node.orelse, candidates, this_ast)
        elif isinstance(node, this_ast.With):
            if this_ast == ast39:
                for item in node.items:
                    open_params = find_open_params_expr(item.context_expr, candidates, this_ast)
                    if open_params:
                        break
            else:
                open_params = find_open_params_expr(node.context_expr, candidates, this_ast)
            if not open_params:
                open_params = find_open_params(node.body, candidates, this_ast)
        if open_params:
            return open_params
    return None


def find_open_params_expr(expr, candidates, this_ast):
    open_params = None
    if isinstance(expr, this_ast.Call) and is_open_call(expr.func, candidates, this_ast):
        open_params = get_kwarg_params(expr, this_ast)

    return open_params


def is_open_call(expr, candidates, this_ast):
    func_name = get_func(expr, this_ast)
    for candidate in candidates:
        if candidate in func_name:
            return False  # io.open or codecs.open
    parts = func_name.split(".")
    if "open" in parts:
        return True
    return False


def get_func(node, this_ast):
    if isinstance(node, this_ast.Call):
        return get_func(node.func, this_ast)
    if isinstance(node, this_ast.Attribute):
        attr = node.attr
        name = get_func(node.value, this_ast)
        func = f"{name}.{attr}"
        return func
    if isinstance(node, this_ast.Name):
        return node.id
    return None


def get_kwarg_params(node, this_ast):
    if isinstance(node, this_ast.Call):
        func = node.func
        if isinstance(func, this_ast.Attribute) and func.attr == "open":
            return node.keywords
        if isinstance(func, this_ast.Name) and func.id == "open":
            return node.keywords
        return get_kwarg_params(node.func, this_ast)
    if isinstance(node, this_ast.Attribute):
        attr = node.attr
        if attr == "open":
            return node.keywords
        return get_kwarg_params(node.value, this_ast)

    return None


def use_open_encoding_kwarg(path):
    file = open(path)
    code = "".join(file.readlines())
    file.close()
    body, this_ast = ast_parse(code)

    candidates = find_open_candidates(body, this_ast)
    if "open" in candidates:
        return False  # open points to io.open or codecs.open

    open_params = find_open_params(body, candidates, this_ast)
    if not open_params:
        return False

    for param in open_params:
        if not param.arg:
            pass
        if param.arg == "encoding":
            return True
    return False




