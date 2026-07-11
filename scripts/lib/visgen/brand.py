"""Active brand-source resolution - the injection seam that lets a working repo
supply its own theme without touching shared code. The engine and brand-lint
both resolve their brand root here, so render and lint can never disagree on the
palette. Resolution order:
  1. VISGEN_BRAND env var (set by a CLI --brand flag or the caller)
  2. <cwd>/brand if it has tokens.json (a working repo's own theme)
  3. the submodule's own brand/ (default VISEMI theme)
Brand is threaded as an env var, not a function argument, to avoid adding a
brand parameter to every render/lint function (ponytail: env carrier)."""
import os
from pathlib import Path

DEFAULT_BRAND = Path(__file__).resolve().parents[3] / "brand"


def active_brand_dir() -> Path:
    env = os.environ.get("VISGEN_BRAND")
    if env:
        return Path(env)
    cwd_brand = Path.cwd() / "brand"
    if (cwd_brand / "tokens.json").is_file():
        return cwd_brand
    return DEFAULT_BRAND
