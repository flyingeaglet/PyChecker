import argparse
from pychecker.check import check_project, check_pkgver, print_results


parser = argparse.ArgumentParser(
    description="PyChecker: check whether your project's Require-Python is correct"
)

package_group = parser.add_argument_group("package")
package_group.add_argument("-p", "--package", help="Package name")
package_group.add_argument("-v", "--version", help="Version of the package")

project_group = parser.add_argument_group("project")
project_group.add_argument("-r", "--root", help="Root path of the project")
project_group.add_argument("-c", "--python_requires", help="python_requires expression")


def main(args=None):
    args = parser.parse_args(args)
    if args.package and args.version:
        # check a PyPI package
        results = check_pkgver(args.package, args.version)
    elif args.root and args.python_requires:
        # check a local project
        results = check_project(args.path, args.python_requires)
    else:
        print(parser.print_help())
        results = None
    if results:
        print_results(results)
