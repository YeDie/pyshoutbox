#!/usr/bin/python3.4

from pyshoutbox import __version__

try:
	from setuptools import setup

except ImportError as err:
	from distutils.core import setup

packages = [
	"pyshoutbox"
]

requires = ["requests>=2.2.1"]

setup(
	name="requests",
	version = __version__,
	description = "Python iShoutbox Parser",
	author = "Benjamin Sparr",
	url = "",
	packages = packages,
	package_dir = {"pyshoutbox": "pyshoutbox"},
	install_requires = requires,
	license = "Public domain",
	zip_safe = False
)
