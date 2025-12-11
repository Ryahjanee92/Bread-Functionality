#!/usr/bin/env python3
"""
Auto-commit script: watches the git working tree for changes, commits them,
and pushes to the configured remote/branch.

Usage:
  python scripts/autocommit.py [--interval SECONDS] [--remote origin] [--branch main]

Notes:
- This script is intended for development convenience only.
- It uses simple polling (not inotify) and relies on the `git` CLI being installed.
"""
import argparse
import subprocess
import time
from datetime import datetime
import shlex
import sys

def run(cmd, cwd=None, capture_output=True):
    try:
        result = subprocess.run(shlex.split(cmd), cwd=cwd, check=True, capture_output=capture_output, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if capture_output and e.stdout:
            print(e.stdout)
        if capture_output and e.stderr:
            print(e.stderr, file=sys.stderr)
        raise

def get_status():
    return run('git status --porcelain')

def get_branch():
    return run('git rev-parse --abbrev-ref HEAD')

def get_unstaged_files():
    out = get_status()
    if not out:
        return []
    files = [line[3:] for line in out.splitlines() if len(line) > 3]
    return files

def get_git_remote(remote):
    try:
        run(f'git ls-remote --exit-code {remote}')
        return remote
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=float, default=2.0, help='Polling interval in seconds')
    parser.add_argument('--remote', default='origin', help='Git remote to push to')
    parser.add_argument('--branch', default=None, help='Git branch to push to (defaults to current)')
    args = parser.parse_args()

    try:
        branch = args.branch or get_branch()
    except Exception:
        print('Failed to determine branch. Ensure you are in a git repo and git is installed.', file=sys.stderr)
        sys.exit(1)

    remote = get_git_remote(args.remote)
    if not remote:
        print(f'Warning: remote {args.remote} not found; will use {args.remote} for push anyway')
        remote = args.remote

    last_status = get_status()
    print(f'Watching repository on branch {branch} (remote: {remote}). Press Ctrl-C to stop.')
    try:
        while True:
            status = get_status()
            if status != last_status and status.strip() != '':
                files = get_unstaged_files()
                msg = f'Auto-commit: {datetime.utcnow().isoformat()} UTC - ' + ', '.join(files[:10])
                print(f'Changes detected. Staging and committing... ({len(files)} files)')
                try:
                    run('git add -A')
                    run(f'git commit -m "{msg}"')
                    print('Committed. Pushing...')
                    run(f'git push {remote} {branch}')
                    print('Push complete')
                except Exception as e:
                    print('Auto-commit failed:', str(e), file=sys.stderr)
                last_status = get_status()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nStopping autocommit watcher')

if __name__ == '__main__':
    main()
