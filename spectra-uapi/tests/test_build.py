import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("build_headers", Path(__file__).resolve().parents[1] / "build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class TestBuild(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.root = Path(self.directory.name)
    self.package = self.root / "spectra_uapi"
    self.package.mkdir()
    self.content = b"/* pinned header */\n"
    self.digest = hashlib.sha256(self.content).hexdigest()
    manifest = {"agnos": {"repository": "https://github.com/example/kernel", "revision": "a" * 40,
                          "files": {"include/media/cam_defs.h": {"path": "include/uapi/media/cam_defs.h",
                                                                 "sha256": self.digest}}}}
    (self.package / "sources.json").write_text(json.dumps(manifest))
    self.installed = self.package / "install/agnos/include/media/cam_defs.h"
    self.patch = patch.multiple(builder, ROOT=self.root, PACKAGE=self.package)
    self.patch.start()
    self.addCleanup(self.patch.stop)

  def test_download_then_offline_sdist_rebuild(self):
    with patch.object(builder.urllib.request, "urlopen", return_value=io.BytesIO(self.content)) as request:
      builder.build()
      request.assert_called_once_with(
        f"https://raw.githubusercontent.com/example/kernel/{'a' * 40}/include/uapi/media/cam_defs.h", timeout=60)
    self.assertEqual(self.installed.read_bytes(), self.content)
    shutil.rmtree(self.root / "headers-src")
    with patch.object(builder.urllib.request, "urlopen", side_effect=AssertionError("network unavailable")):
      builder.build()
    self.assertEqual(self.installed.read_bytes(), self.content)

  def test_bad_download_preserves_previous_install(self):
    self.installed.parent.mkdir(parents=True)
    self.installed.write_bytes(b"previous version")
    with patch.object(builder.urllib.request, "urlopen", return_value=io.BytesIO(b"wrong source")):
      with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
        builder.build()
    self.assertEqual(self.installed.read_bytes(), b"previous version")

  def test_corrupt_cache_is_refetched_and_stale_files_removed(self):
    cache = self.root / "headers-src"
    cache.mkdir()
    (cache / self.digest).write_bytes(b"corrupt cache")
    self.installed.parent.mkdir(parents=True)
    stale = self.installed.with_name("stale.h")
    stale.write_bytes(b"old header")
    with patch.object(builder.urllib.request, "urlopen", return_value=io.BytesIO(self.content)) as request:
      builder.build()
      request.assert_called_once()
    self.assertEqual(self.installed.read_bytes(), self.content)
    self.assertFalse(stale.exists())


if __name__ == "__main__":
  unittest.main(verbosity=2)
