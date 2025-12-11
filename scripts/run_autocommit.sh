#!/usr/bin/env bash
# Simple wrapper to run autocommit in the background
python3 scripts/autocommit.py --interval 2 &
echo $! > .autocommit.pid
echo "Autocommit started (PID $(cat .autocommit.pid)). To stop: kill $(cat .autocommit.pid) && rm .autocommit.pid"
