"""Dev-server launchers, exposed as console scripts.

The React interface is two processes: this starts the vite dev server, which
proxies /api through to the FastAPI server (see frontend/vite.config.ts). Run
the API in a second terminal.
"""
import shutil
import subprocess
import sys
from pathlib import Path

# api/movie_api/dev.py -> api/movie_api -> api -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"


def web() -> int:
    """Start the React dev server (vite) in frontend/."""
    if not FRONTEND.is_dir():
        sys.exit(f"No frontend directory at {FRONTEND}")

    # npm is npm.cmd on Windows, which subprocess will not find without the
    # full path unless we resolve it first.
    npm = shutil.which("npm")
    if npm is None:
        sys.exit("npm was not found on PATH. Install Node.js: https://nodejs.org")

    if not (FRONTEND / "node_modules").is_dir():
        print("frontend/node_modules is missing; installing first...")
        result = subprocess.run([npm, "install"], cwd=FRONTEND)
        if result.returncode != 0:
            return result.returncode

    print(f"Starting the React dev server in {FRONTEND}")
    try:
        return subprocess.run([npm, "run", "dev"], cwd=FRONTEND).returncode
    except KeyboardInterrupt:
        return 0
