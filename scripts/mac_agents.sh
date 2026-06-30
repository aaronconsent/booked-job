#!/bin/bash
# Stop (or restart) the Mac's launchd agents. After you've confirmed the GitHub
# Actions workflow works, run `bash scripts/mac_agents.sh off` so the Mac stops
# posting and Actions becomes the sole host. Fully reversible with `on`.
ACTION="${1:-off}"
n=0
for p in ~/Library/LaunchAgents/com.bookedjob.*.plist; do
  [ -f "$p" ] || continue
  name=$(basename "$p" .plist)
  if [ "$ACTION" = "off" ]; then
    launchctl unload "$p" 2>/dev/null && { echo "  stopped $name"; n=$((n+1)); }
  else
    launchctl load "$p" 2>/dev/null && { echo "  started $name"; n=$((n+1)); }
  fi
done
echo "Done — ${ACTION^^} for $n Mac agents. $([ "$ACTION" = off ] && echo 'GitHub Actions is now the host.' || echo 'Mac agents are running again.')"
