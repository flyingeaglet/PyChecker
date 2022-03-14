import pychecker.config as config
import os
from pychecker.utils import read_object_from_file
from functools import reduce
from pychecker.check.common import analysis, parse_import_modules


std_modules = read_object_from_file(os.path.join(config.CACHE_DIR, "standard_top_level.json"))
std_module_set = set(reduce(lambda x, y: set(x).union(set(y)), std_modules.values()))  # union, or intersection
setup_modules = {"setuptools", "distutils", "pkg_resources", "pip", "wheel", "__future__"}


def has_extra_deps(path, **kwargs):
    custom_modules = kwargs["custom_modules"] if "custom_modules" in kwargs else set()
    pyver = kwargs["pyver"] if "pyver" in kwargs else None
    is_setup = kwargs["is_setup"] if "is_setup" in kwargs else False
    file = open(path)
    code = "".join(file.readlines())
    file.close()
    modules = parse_import_modules(code, is_setup)
    if pyver is None:
        module_set = std_module_set
    else:
        module_set = std_modules[pyver]
    module_set = module_set.union(setup_modules)
    if custom_modules is None:
        custom_modules = set()
    module_set = module_set.union(custom_modules)
    for module, level in modules:
        if level != 0:
            continue
        top_name = module.split(".")[0]
        if top_name not in module_set:
            return True  # include third-party modules
    return False


def detect_extra_deps(path, custom_modules=None, pyver=None, is_setup=False):
    if not custom_modules:
        custom_modules = set()
    return analysis(path, has_extra_deps, custom_modules=custom_modules, pyver=pyver, is_setup=is_setup)
