#!/bin/bash
# Refresh dashboard stats and push so the deployed dashboard stays live.
cd /Users/aaronphillips/GIT/booked-job || exit 1
/usr/bin/python3 scripts/fetch_stats.py
git add site/dashboard/data.json site/dashboard/changelog.json 2>/dev/null
if ! git diff --cached --quiet 2>/dev/null; then
  git commit -q -m "dashboard: refresh stats" 2>/dev/null
  git push -q 2>/dev/null && echo "pushed" || echo "push failed (will retry next run)"
else
  echo "no changes"
fi
