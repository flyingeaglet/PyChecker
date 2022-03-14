import os
import time
import pychecker.config as config
from pychecker.check.no_avl_resource_detection import detect_no_avl_resource_pkg, parse_comp_expr
from pychecker.check.visit_pypi import parse_whl_comp, get_source_url, download_extract_source, get_metadata, COMP
from pychecker.check.incomp_feature_detection import detect_incomp_feature_usage
from pychecker.check.local_comp_detection import detect_local_comp_detection
from pychecker.check.common import find_custom_modules


def check_pkgver(pkg, ver, cache_path=None):
    results = [False, False, False]
    metadata = get_metadata(pkg, ver)
    if not metadata:
        return results
    pyvers = set(parse_comp_expr(metadata[COMP], config.PY_VERSIONS))
    results[2] = detect_no_avl_resource_pkg(pkg, ver)
    wheel_pyvers = parse_whl_comp(pkg, ver)
    no_wheel_pyvers = pyvers-wheel_pyvers-{"3.10"}  # TODO: 3.10
    if not no_wheel_pyvers:
        return results

    # detect FEATURE & LOCAL for source code resources
    path1 = os.path.join(cache_path, f"{pkg}-{ver}")
    path2 = os.path.join(cache_path, f"{pkg.replace('-', '_')}-{ver}")
    path = path1 if os.path.exists(path1) else path2
    if not os.path.exists(path):
        source_url = get_source_url(pkg, ver)
        if not source_url:
            return results  # no source code
        download_extract_source(source_url, path)
        time.sleep(5)
        path = path1 if os.path.exists(path1) else path2

    setup_path = os.path.join(path, "setup.py")
    if not os.path.exists(setup_path):
        print("*"*10, pkg, ver, "*"*10)  # bad directory structure, need manual help!!
        return results
    results[1] = detect_local_comp_detection(setup_path)

    custom_modules = find_custom_modules(path)
    if not custom_modules:
        print("*"*10, pkg, ver, "*"*10)  # bad directory structure, need manual help!!
        return results
    results[0] = detect_incomp_feature_usage(setup_path, no_wheel_pyvers, custom_modules)
    return results

