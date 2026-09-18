import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist


def fetch_headers():
  subprocess.check_call([sys.executable, "build.py"], cwd=Path(__file__).parent)


class BuildHeaders(build_py):
  def run(self):
    fetch_headers()
    super().run()


class SourceHeaders(sdist):
  def run(self):
    fetch_headers()
    super().run()


setup(cmdclass={"build_py": BuildHeaders, "sdist": SourceHeaders})
