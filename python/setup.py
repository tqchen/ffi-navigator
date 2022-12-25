from distutils.core import setup
from setuptools import find_packages

setup(
    name = "ffi-navigator",
    version = "0.5.4",
    license="Apache-2.0",
    description = "Language server for navigating FFI calls",
    author = "FFI navigator contributors",
    author_email = "tianqi.tchen@gmail.com",
    url = "https://github.com/tqchen/ffi-navigator",
    keywords = [],
    packages = find_packages(),
    install_requires = [
        "python-jsonrpc-server",
        "attrs"
    ],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
  ],
)
