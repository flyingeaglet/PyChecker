import os
import re
import pychecker.config as config
from pychecker.utils import read_object_from_file
from pychecker.check.common import analysis, ast_parse, parse_import_modules, get_func, parse_func_params
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


def find_import_open_candidates(code):
    modules = parse_import_modules(code, True)
    modules = [module[0] for module in modules]
    candidates = [module for module in modules
                  if module == "io" or module == "io.open" or module == "codecs" or module == "codecs.open"]
    return candidates


def is_open_call(expr, this_ast, candidates):
    func_name = get_func(expr, this_ast)
    for candidate in candidates:
        if candidate in func_name:
            return False  # io.open or codecs.open
    parts = func_name.split(".")
    if "open" in parts:
        return True
    return False


def use_open_encoding_kwarg(path):
    file = open(path)
    code = "".join(file.readlines())
    file.close()
    body, this_ast = ast_parse(code)

    candidates = find_import_open_candidates(code)
    if "io.open" in candidates or "codecs.open" in candidates:
        return False

    # open_params = find_open_params(body, candidates, this_ast)
    open_params = parse_func_params(body, this_ast, "open", is_open_call, candidates)
    if not open_params:
        return False

    for param in open_params:
        if not param.arg:
            pass
        if param.arg == "encoding":
            return True
    return False




