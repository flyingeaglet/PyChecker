import os
from setuptools import setup, find_packages


here = os.path.dirname(__file__)
requirement = os.path.join(here, "requirements.txt")
readme = os.path.join(here, "README.md")
deps = open(requirement).readlines()
desc = open(readme).read()

setup(
    name="pychecker",
    version="0.0.2a0",
    description="PyChecker: check whether your project's Require-Python is correct",
    long_description=desc,
    url="https://github.com/PyVCEchecker/PyVCEchecker",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.6",
    install_requires=deps,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pychecker = pychecker.checker:main",
        ]
    },
    package_data={
        "pychecker.cache": ["*.json"]
    }
)
