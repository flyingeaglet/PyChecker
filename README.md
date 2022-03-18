# PyChecker
PyChecker: check whether your project's Require-Python is correct

## Installation
* Clone this repository
```bash
git clone https://github.com/PyVCEchecker/PyVCEchecker.git
```
* Install local (requires Python>=3.6)
```bash
cd PyVCEchecker
python setup.py install
```

## Instructions
```bash
pychecker

usage: pychecker [-h] [-p PACKAGE] [-v VERSION] [-r ROOT] [-c PYTHON_REQUIRES]
                 [-d INSTALL_REQUIRES]

PyChecker: check whether your project's Require-Python is right

optional arguments:
  -h, --help            show this help message and exit

package:
  -p PACKAGE, --package PACKAGE
                        Package name
  -v VERSION, --version VERSION
                        Version of the package

project:
  -r ROOT, --root ROOT  Root path of the project
  -c PYTHON_REQUIRES, --python_requires PYTHON_REQUIRES
                        python_requires expression
  -d INSTALL_REQUIRES, --install_requires INSTALL_REQUIRES
                        Path of requirements.txt
```
For example, 
```bash
pychecker -p django-chroniker -v 1.0.22
```

## Empirical Study and Experimental Result
Our empirical study and experimental result can be found [here](https://github.com/PyVCEchecker/Study-Experiment).


## PyPI Release
Coming soon.