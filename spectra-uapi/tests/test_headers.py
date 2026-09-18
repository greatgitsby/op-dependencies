"""Run against an installed wheel, not the source-tree package."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

import spectra_uapi

HERE = Path(__file__).resolve().parent
CC = shlex.split(os.environ.get("CC", "cc"))
CXX = shlex.split(os.environ.get("CXX", "c++"))


def flags(abi, compiler):
  result = ["-Wall", "-Wextra", "-Werror", "-I", spectra_uapi.INCLUDE_DIRS[abi],
            "-include", spectra_uapi.COMPAT_HEADERS[abi]]
  if "clang" in subprocess.check_output([*compiler, "--version"], text=True):
    result += ["-Wno-gnu-variable-sized-type-not-at-end"]
  return result


class TestHeaders(unittest.TestCase):
  def test_integrity(self):
    spectra_uapi.smoketest()

  def test_each_header_c_and_cxx(self):
    sources = json.loads((spectra_uapi.DIR / "sources.json").read_text())
    for compiler, language, standard in ((CC, "c", "gnu11"), (CXX, "c++", "gnu++17")):
      for abi, source in sources.items():
        options = flags(abi, compiler)
        for path in source["files"]:
          if not path.startswith("include/"):
            continue
          with self.subTest(abi=abi, header=path, language=language):
            subprocess.run([*compiler, *options, f"-std={standard}", "-x", language, "-fsyntax-only", "-"],
                           input=f"#include <{path.removeprefix('include/')}>\n", text=True, check=True)

  def test_both_abis_link_and_run(self):
    with tempfile.TemporaryDirectory() as directory:
      objects = []
      for abi in spectra_uapi.INCLUDE_DIRS:
        obj = str(Path(directory) / f"{abi}.o")
        subprocess.run([*CXX, *flags(abi, CXX), "-std=gnu++17", f"-DMODERN={int(abi == 'camera_kt')}",
                        "-c", str(HERE / "abi.cc"), "-o", obj], check=True)
        objects.append(obj)
      executable = str(Path(directory) / "dual-abi")
      subprocess.run([*CXX, str(HERE / "link.cc"), *objects, "-o", executable], check=True)
      subprocess.run([executable], check=True)

  def test_wrong_headers_are_rejected(self):
    for abi in spectra_uapi.INCLUDE_DIRS:
      with self.subTest(abi=abi):
        result = subprocess.run([*CXX, *flags(abi, CXX), "-std=gnu++17", f"-DMODERN={int(abi != 'camera_kt')}",
                                 "-fsyntax-only", str(HERE / "abi.cc")], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("static assertion", result.stderr)

  def test_old_linux_flex_array_fallback(self):
    # Suppress the host macro after including stddef; compat must supply it.
    source = '#include <linux/stddef.h>\n#undef __DECLARE_FLEX_ARRAY\n'
    source += f'#include "{spectra_uapi.COMPAT_HEADERS["camera_kt"]}"\n'
    source += '#include <media/cam_sensor.h>\n'
    for compiler, language, standard in ((CC, "c", "gnu11"), (CXX, "c++", "gnu++17")):
      with self.subTest(language=language):
        subprocess.run([*compiler, "-I", spectra_uapi.INCLUDE_DIRS["camera_kt"],
                        f"-std={standard}", "-x", language, "-fsyntax-only", "-"],
                       input=source, text=True, check=True)


if __name__ == "__main__":
  unittest.main(verbosity=2)
