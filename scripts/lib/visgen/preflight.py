"""Branch guard: when the studio runs as a submodule inside a working repo it
must be on a dedicated project branch, never on master/main - so per-project
studio upgrades never accumulate on the shared baseline by accident. Renders are
refused on master/main when a submodule checkout is detected. Standalone use
(a normal clone, .git is a directory) is never blocked; evals call the engine
directly and bypass this guard."""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def running_as_submodule() -> bool:
    # A submodule working tree has a .git FILE ("gitdir: ..."); a clone has a dir.
    return (REPO_ROOT / ".git").is_file()


def current_branch() -> str:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def branch_guard_message(is_submodule: bool, branch: str) -> str | None:
    if is_submodule and branch in ("master", "main"):
        return (f"visual-generation is on '{branch}' as a submodule inside a working "
                "repo. Create a dedicated project branch first: run the visgen-setup "
                "skill, or `git -C visual-generation checkout -b <project>` (e.g. "
                "visemi-catcanh), then retry.")
    return None


def check_branch() -> str | None:
    return branch_guard_message(running_as_submodule(), current_branch())
