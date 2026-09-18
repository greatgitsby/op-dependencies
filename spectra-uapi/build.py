"""Fetch only the pinned camera headers and licenses; never a whole kernel tree."""
import hashlib
import json
import shutil
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "spectra_uapi"


def build():
  sources = json.loads((PACKAGE / "sources.json").read_text())
  cache = ROOT / "headers-src"
  cache.mkdir(exist_ok=True)

  def fetch(item):
    destination, source, entry = item
    cached = cache / entry["sha256"]
    if not cached.exists() or hashlib.sha256(cached.read_bytes()).hexdigest() != entry["sha256"]:
      installed = PACKAGE / "install" / destination.relative_to(staging)
      if installed.is_file() and hashlib.sha256(installed.read_bytes()).hexdigest() == entry["sha256"]:
        data = installed.read_bytes()
      else:
        repository = entry.get("repository", source["repository"]).removeprefix("https://github.com/")
        revision = entry.get("revision", source["revision"])
        url = f"https://raw.githubusercontent.com/{repository}/{revision}/{entry['path']}"
        with urllib.request.urlopen(url, timeout=60) as response:
          data = response.read()
      if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {entry['path']}")
      cached.write_bytes(data)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cached, destination)

  # A failed download must not leave a partially populated install tree.
  with tempfile.TemporaryDirectory(dir=PACKAGE) as staging:
    tasks = [(Path(staging) / abi / name, source, entry)
             for abi, source in sources.items() for name, entry in source["files"].items()]
    with ThreadPoolExecutor(max_workers=8) as pool:
      list(pool.map(fetch, tasks))
    install = PACKAGE / "install"
    if install.exists():
      shutil.rmtree(install)
    shutil.move(staging, install)


if __name__ == "__main__":
  build()
