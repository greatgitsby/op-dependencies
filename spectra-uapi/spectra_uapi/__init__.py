import hashlib
import json
from pathlib import Path

DIR = Path(__file__).resolve().parent
INCLUDE_DIRS = {abi: str(DIR / "install" / abi / "include") for abi in ("agnos", "camera_kt")}
COMPAT_HEADERS = {abi: str(DIR / "compat" / f"{abi}.h") for abi in INCLUDE_DIRS}


def smoketest():
  """Validate wheel contents without requiring a compiler or Linux host headers."""
  sources = json.loads((DIR / "sources.json").read_text())
  for abi, source in sources.items():
    for name, entry in source["files"].items():
      path = DIR / "install" / abi / name
      if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise RuntimeError(f"Missing or corrupt Spectra dependency: {path}")
    if not Path(COMPAT_HEADERS[abi]).is_file():
      raise RuntimeError(f"Missing Spectra compatibility header: {abi}")
