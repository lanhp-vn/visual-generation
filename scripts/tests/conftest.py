"""Pytest config: put the scripts/ layers on sys.path (same pattern as cat-canh).
Engine modules are imported as `from visgen.x import ...`."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for sub in ("lib", "util", "ops"):
    p = ROOT / "scripts" / sub
    if p.is_dir():
        sys.path.insert(0, str(p))
