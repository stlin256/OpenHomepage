"""Render the Flask homepage into a self-contained static site.

The application performs its cache warm-up before it starts listening. Keep
the server alive until the HTTP endpoint is actually ready, and fail the
build when no valid entry page was produced. Publishing an empty dist
directory makes GitHub Pages return a misleading 404.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
APP = ROOT / "app.py"
PORT = int(os.environ.get("OPENHOMEPAGE_PORT", "8004"))
HEALTH_URL = f"http://127.0.0.1:{PORT}/"
STARTUP_TIMEOUT = float(os.environ.get("OPENHOMEPAGE_STARTUP_TIMEOUT", "600"))
POLL_INTERVAL = float(os.environ.get("OPENHOMEPAGE_POLL_INTERVAL", "2"))


def clean_dist() -> None:
    """Remove a previous generated tree so stale HTML cannot be published."""
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)


def stop_process(proc: subprocess.Popen[bytes]) -> None:
    """Terminate the child and guarantee it is reaped on every platform."""
    if proc.poll() is not None:
        return

    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=15)


def fetch_homepage(server: subprocess.Popen[bytes]) -> bytes:
    """Wait for Flask and return a non-empty HTML response."""
    deadline = time.monotonic() + STARTUP_TIMEOUT
    attempt = 0

    while time.monotonic() < deadline:
        attempt += 1
        if server.poll() is not None:
            raise RuntimeError(
                f"app.py exited before becoming ready (exit code {server.returncode})"
            )

        try:
            with urlopen(HEALTH_URL, timeout=10) as response:
                body = response.read()
                content_type = response.headers.get("Content-Type", "")
                if response.status != 200:
                    raise RuntimeError(
                        f"homepage returned HTTP {response.status} while generating"
                    )
                if not body.strip():
                    raise RuntimeError("homepage returned an empty response")
                if "html" not in content_type.lower() and b"<html" not in body.lower():
                    raise RuntimeError("homepage response is not HTML")
                return body
        except HTTPError as exc:
            last_error = f"HTTP {exc.code}"
        except (URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
        except RuntimeError:
            raise

        if attempt == 1 or attempt % 10 == 0:
            remaining = max(0, int(deadline - time.monotonic()))
            print(f"Waiting for Flask ({remaining}s remaining): {last_error}", flush=True)
        time.sleep(POLL_INTERVAL)

    raise TimeoutError(
        f"Flask did not become ready within {STARTUP_TIMEOUT:.0f}s at {HEALTH_URL}"
    )


def main() -> int:
    if not APP.is_file():
        raise FileNotFoundError(f"Application entrypoint not found: {APP}")

    clean_dist()
    print(f"Starting {APP.name} with {sys.executable}...", flush=True)
    environment = os.environ.copy()
    environment['OPENHOMEPAGE_INITIAL_SYNC'] = 'foreground'
    environment['OPENHOMEPAGE_PORT'] = str(PORT)
    environment['OPENHOMEPAGE_STATIC_BUILD'] = '1'
    server = subprocess.Popen(
        [sys.executable, str(APP)],
        cwd=ROOT,
        stdout=None,
        stderr=None,
        env=environment,
    )

    try:
        body = fetch_homepage(server)
        output = DIST / "index.html"
        temporary = DIST / ".index.html.tmp"
        temporary.write_bytes(body)
        temporary.replace(output)

        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(f"Generated entry page is missing or empty: {output}")
        print(f"Generated {output} ({output.stat().st_size} bytes)", flush=True)
        return 0
    finally:
        stop_process(server)


if __name__ == "__main__":
    try:
        exit_code = main()
    except BaseException:
        # Never leave a partial page behind for the deploy step to publish.
        if DIST.exists():
            shutil.rmtree(DIST, ignore_errors=True)
        raise
    raise SystemExit(exit_code)
