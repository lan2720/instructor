import os
import sys
import pkg_resources
from setuptools import setup, find_packages
import subprocess


pkg_resources.require(['pip >= 21.2.4'])
pip_cmd = os.path.join(os.path.dirname(sys.executable), "pip")


def install_package(pkg, shell=False):
    try:
        subprocess.check_call([pip_cmd, 'install', pkg], shell=shell)
    except:
        print(f"fail to install {pkg}")
    print(f"installing {pkg} finished.")


def process_requirements():
    print("进入process_requirements")
    packages = open('requirements.txt').read().splitlines()
    requires = []

    for pkg in packages:
        install_package(pkg)

    return requires


setup(name='instructor',
      description='instructor by jxnl',
      version='0.4.6rc1',
      author='jarvixwang',
      packages=find_packages(),
      package_dir={'instructor': 'instructor'},
      package_data={'instructor': ['*.*']},
      include_package_data=True,
      install_requires=[],
      )
