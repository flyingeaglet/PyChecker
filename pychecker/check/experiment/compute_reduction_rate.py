from pychecker.check.no_avl_resource_detection import parse_dep_expr2
from pychecker.utils import read_object_from_file


def compute_ver_opt(metadata):
    versions = 0
    for value in metadata.values():
        versions += len(value)
    return versions


def compute_ver_total(metadata, pkgver):
    used_pkgver = dict()
    for pkg, ver_dict in metadata.items():
        if pkg not in used_pkgver:
            used_pkgver[pkg] = set()
        for ver in ver_dict.keys():
            used_pkgver[pkg].add(ver)
            deps = ver_dict[ver]["requires_dist"]
            for dep in deps:
                d, versions = parse_dep_expr2(dep, pkgver)
                if not d:
                    continue
                if d not in used_pkgver:
                    used_pkgver[d] = set()
                used_pkgver[d] = used_pkgver[d].union(set(versions))

    versions = 0
    max_count = 0
    max_pkg = None
    for key, value in used_pkgver.items():
        if len(value) > max_count:
            max_pkg = key
            max_count = len(value)
        versions += len(value)
    return versions, max_pkg, max_count


if __name__ == '__main__':
    metadata = read_object_from_file("exp_cache/metadata_cache-lab-all.json")
    pkgver = read_object_from_file("exp_cache/pkgver_cache-lab-all.json")
    ver_opt = compute_ver_opt(metadata)
    ver_total, max_pkg, max_count = compute_ver_total(metadata, pkgver)
    print("*"*10, "In the Lab", "*"*10)
    print(f"{len(metadata.keys())} packages, {ver_total} -> {ver_opt}, {ver_opt/ver_total}")
    print(f"Max count: {max_pkg}-{max_count} versions, {len(metadata[max_pkg])} versions after opt")

    metadata = read_object_from_file("exp_cache/metadata_cache-field-all.json")
    pkgver = read_object_from_file("exp_cache/pkgver_cache-field-all.json")
    ver_opt = compute_ver_opt(metadata)
    ver_total, max_pkg, max_count = compute_ver_total(metadata, pkgver)
    print("*" * 10, "In the Field", "*" * 10)
    print(f"{len(metadata.keys())} packages, {ver_total} -> {ver_opt}, {ver_opt/ver_total}")
    print(f"Max count: {max_pkg}-{max_count} versions, {len(metadata[max_pkg])} versions after opt")
