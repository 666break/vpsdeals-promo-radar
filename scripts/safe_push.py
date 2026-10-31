#!/usr/bin/env python3
"""Push to main the only way two scheduled jobs may push: rebase first, retry, never force.

Why this exists
---------------
Two daily jobs (07:30 vps-price shift, 11:00 a2-hosting shift) both commit into this
repo. They append to the same files (live-site/sitemap.xml, live-site/_redirects), so a
plain `git push` from the second one is rejected as non-fast-forward, and a retry loop
that ignores the rebase can lose the other job's work. This script is the single
sanctioned path: always rebase onto origin/main, at most 3 attempts with backoff,
abort the rebase on conflict, log every attempt, and never use --force.

Usage
-----
  python scripts/safe_push.py -m "post: <slug> — <title> (YYYY-MM-DD)"
      commit everything already staged, then rebase + push
  python scripts/safe_push.py
      push what is already committed (no new commit)

Exit codes
----------
  0  pushed (or nothing to push)
  1  gave up after 3 attempts, or a rebase conflict — nothing was force-pushed
  2  bad usage / not a git repo

Rules this script enforces
--------------------------
  * `git pull --rebase origin main` before every attempt
  * backoff 5s, 20s, 60s between attempts
  * `git rebase --abort` on conflict, then exit 1
  * no `--force`, no `--no-verify`, no `git add -A` (caller stages)
  * every attempt appended to .workbuddy-ai/memory/safe_push.log
"""

import argparse
import datetime
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / ".workbuddy-ai" / "memory" / "safe_push.log"
BRANCH = "main"
ATTEMPTS = 3
BACKOFF = (5, 20, 60)


def run(args):
    """Run one git command, return (code, combined output)."""
    p = subprocess.run(["git"] + args, cwd=str(REPO), capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def log(line):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{stamp}  {line}\n")


def main():
    ap = argparse.ArgumentParser(description="rebase-then-push, max 3 attempts, never force")
    ap.add_argument("-m", "--message", help="commit staged changes with this message first")
    args = ap.parse_args()

    code, _ = run(["rev-parse", "--git-dir"])
    if code != 0:
        print("not a git repository", file=sys.stderr)
        return 2

    if args.message:
        code, out = run(["diff", "--cached", "--quiet"])
        if code == 0:
            print("nothing staged — pass nothing to -m, or stage files first")
        else:
            code, out = run(["commit", "-m", args.message])
            print(out)
            if code != 0:
                log(f"COMMIT FAILED  {args.message[:80]}")
                return 1

    for attempt in range(1, ATTEMPTS + 1):
        code, out = run(["pull", "--rebase", f"origin", BRANCH])
        if code != 0:
            print(f"[attempt {attempt}/{ATTEMPTS}] pull --rebase failed:\n{out}")
            run(["rebase", "--abort"])
            log(f"REBASE CONFLICT attempt={attempt}  aborted, nothing pushed")
            print("rebase aborted; resolve by hand — refusing to force anything", file=sys.stderr)
            return 1

        code, out = run(["push", "origin", f"HEAD:{BRANCH}"])
        if code == 0:
            _, sha = run(["rev-parse", "--short", "HEAD"])
            print(f"[attempt {attempt}/{ATTEMPTS}] pushed {sha}")
            log(f"OK attempt={attempt} sha={sha}")
            return 0

        print(f"[attempt {attempt}/{ATTEMPTS}] push rejected:\n{out}")
        log(f"PUSH REJECTED attempt={attempt}")
        if attempt < ATTEMPTS:
            time.sleep(BACKOFF[attempt - 1])

    log(f"GAVE UP after {ATTEMPTS} attempts — nothing pushed, no force used")
    print(f"gave up after {ATTEMPTS} attempts; see {LOG}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
