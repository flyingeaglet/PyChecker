from functools import cmp_to_key
from pychecker.check.visit_pypi import get_metadata, get_pkg_versions, DEPS, COMP
from pychecker.check.common import compare_version
import pychecker.config as config


def detect_no_avl_resource_pkg(pkg, ver):
    metadata = get_metadata(pkg, ver)
    if not metadata:
        return False
    dep_exprs = metadata[DEPS]
    comp_expr = metadata[COMP]
    visited_lower = {f"{pkg}#{ver}"}
    visited_upper = {f"{pkg}#{ver}"}
    return detect_no_avl_resource(comp_expr, dep_exprs, visited_lower, visited_upper)


def detect_no_avl_resource(comp_expr, dep_exprs, visited_lower=None, visited_upper=None):
    comp_info = parse_comp_expr(comp_expr, config.PY_VERSIONS)
    comp_info = sorted(comp_info, key=cmp_to_key(compare_version))
    if not visited_lower:
        visited_lower = set()
    if not visited_upper:
        visited_upper = set()
    for expr in dep_exprs:
        dep, lower, upper = parse_dep_expr(expr)
        if not dep:
            continue
        if not lower_comp(dep, lower, comp_info[0], visited_lower):
            # pass  # to get the full problem domain
            return True
        if not upper_comp(dep, upper, comp_info[-1], visited_upper):
            # pass
            return True
    return False


def lower_comp(pkg, ver, pyver, visited):
    # print("low", pkg, ver)
    # if len(visited) > 100:
    #     return True  # prevent stackoverflow
    metadata = get_metadata(pkg, ver)
    if not metadata:
        return True
    dep_exprs = metadata[DEPS]
    comp_expr = metadata[COMP]
    comp_info = parse_comp_expr(comp_expr, config.PY_VERSIONS)
    comp_info = sorted(comp_info, key=cmp_to_key(compare_version))
    if pyver < comp_info[0]:
        return False
    visited.add(f"{pkg}#{ver}")
    for expr in dep_exprs:
        dep, lower, _ = parse_dep_expr(expr)
        if not dep:
            continue
        pkgver = f"{dep}#{lower}"
        if pkgver in visited:
            continue  # prevent circuit
        if not lower_comp(dep, lower, pyver, visited):
            return False
    return True


def upper_comp(pkg, ver, pyver, visited):
    # print("up", pkg, ver)
    # if len(visited) > 100:
    #     return True  # prevent stackoverflow
    metadata = get_metadata(pkg, ver)
    if not metadata:
        return True
    dep_exprs = metadata[DEPS]
    comp_expr = metadata[COMP]
    comp_info = parse_comp_expr(comp_expr, config.PY_VERSIONS)
    comp_info = sorted(comp_info, key=cmp_to_key(compare_version))
    if pyver > comp_info[-1]:
        return False
    visited.add(f"{pkg}#{ver}")
    for expr in dep_exprs:
        dep, _, upper = parse_dep_expr(expr)
        if not dep:
            continue
        pkgver = f"{dep}#{upper}"
        if pkgver in visited:
            continue  # prevent circuit
        if not upper_comp(dep, upper, pyver, visited):
            return False
    return True


def parse_comp_expr(expr, versions):
    # comp_expr: <=version, >=version, ...
    conditions = expr.split(",")
    satisfied_versions = list()
    for version in versions:
        satisfied = True
        for condition in conditions:
            if not judge_condition(version, condition):
                satisfied = False
                break
        if satisfied:
            satisfied_versions.append(version)
    return satisfied_versions


def parse_dep_expr(expr):
    # dep_expr: pkg (comp_expr) [; condition] | pkg comp_expr [; condition]
    dep, expr = split_dep_expr(expr)
    if not dep:
        return None, None, None

    versions = get_pkg_versions(dep)
    if not versions:
        return None, None, None
    comp_versions = parse_comp_expr(expr, versions)
    comp_versions = sorted(comp_versions, key=cmp_to_key(compare_version))
    if len(comp_versions) == 0:
        print(dep, expr)  # what happened?
        return None, None, None
    return dep, comp_versions[0], comp_versions[-1]


def split_dep_expr(expr):
    if ";" in expr:
        return None, None  # conditional dependency, not consider now
    try:
        condition_start = expr.index("(")
        condition_end = expr.index(")")
    except ValueError:
        condition_start = len(expr)
        condition_end = condition_start
    dep = expr[:condition_start].strip()
    try:
        option_start = dep.index("[")
        dep = dep[:option_start].strip()
    except ValueError:
        pass
    condition = expr[condition_start:condition_end].strip()
    condition = condition.removeprefix("(").removesuffix(")")

    symbols = [">=", "<=", ">", "<", "==", "!=", "~="]
    this_symbol = None
    for symbol in symbols:
        try:
            condition_start = dep.index(symbol)
            this_symbol = symbol
        except ValueError:
            continue
    if this_symbol:
        condition = dep[condition_start:]
        dep = dep[:condition_start]

    return dep, condition


def judge_condition(version, condition):
    symbols = [">=", "<=", ">", "<", "==", "!=", "~="]
    this_symbol = None
    for symbol in symbols:
        try:
            condition.index(symbol)
            this_symbol = symbol
            break
        except ValueError:
            continue

    if not this_symbol:
        return True  # condition = "", return True

    compare_to_version = condition.replace(this_symbol, "").strip()
    compare_to_version = compare_to_version.replace("'", "").replace('"', '')
    if this_symbol == "~=":
        this_symbol = ">="

    if "*" not in compare_to_version:
        return eval(f"compare_version('{version}', '{compare_to_version}') {this_symbol} 0")
    else:
        # consider == and !=
        aster_ind = compare_to_version.index("*")
        compare_to_version = compare_to_version[:aster_ind]
        tmp_version = version+"."
        if this_symbol == "==":
            return tmp_version.startswith(compare_to_version)
        if this_symbol == "!=":
            return not tmp_version.startswith(compare_to_version)
        if this_symbol == ">" or this_symbol == ">=":
            return eval(f"compare_version('{tmp_version}', '{compare_to_version}') {this_symbol} 0")

    print(version, condition)  # what happened?
    return True

# print(detect_no_avl_resource_pkg("help50", "3.0.5"))