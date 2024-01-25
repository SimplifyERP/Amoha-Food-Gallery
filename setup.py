from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in amohafoodgallery/__init__.py
from amohafoodgallery import __version__ as version

setup(
	name="amohafoodgallery",
	version=version,
	description="Custom development",
	author="VPS Consultancy",
	author_email="vpsconsultancy2020@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
