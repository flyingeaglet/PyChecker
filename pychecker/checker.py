import argparse
from pychecker.check import check_project, check_pkgver


parser = argparse.ArgumentParser(
    description="PyChecker: check whether your project's Require-Python is right"
)

package_group = parser.add_argument_group("package")
package_group.add_argument("-p", "--package", help="Package name")
package_group.add_argument("-v", "--version", help="Version of the package")

project_group = parser.add_argument_group("project")
project_group.add_argument("-r", "--root", help="Root path of the project")
project_group.add_argument("-c", "--python_requires", help="python_requires expression")
project_group.add_argument("-d", "--install_requires", help="Path of requirements.txt")


def main(args=None):
    args = parser.parse_args(args)
    if args.package:
        result = check_pkgver(args.package, args.version)
    elif args.root:
        with open(args.install_requires) as f:
            deps = f.readlines()
        result = check_project(args.path, args.python_requires, deps)
    else:
        print(parser.print_help())
        result = None
    if result:
        print(result)
