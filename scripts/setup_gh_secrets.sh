#!/bin/bash
# One-time: upload every secrets/*.env file to GitHub Actions Secrets as ENV_<NAME>,
# so the automation workflow can recreate them at runtime. Run this once from your Mac.
#
# Prereqs:  brew install gh   &&   gh auth login   (pick GitHub.com, HTTPS)
# Then:     bash scripts/setup_gh_secrets.sh
set -e
cd "$(dirname "$0")/.."
command -v gh >/dev/null || { echo "Install the GitHub CLI first:  brew install gh  &&  gh auth login"; exit 1; }
REPO="aaronconsent/booked-job"
echo "Uploading secrets to $REPO ..."
for f in secrets/*.env; do
  [ -f "$f" ] || continue
  base=$(basename "$f" .env | tr '[:lower:]' '[:upper:]')
  name="ENV_$base"
  gh secret set "$name" --repo "$REPO" < "$f" && echo "  ✓ $name"
done
echo "Done — all env files are now GitHub Actions secrets. The workflow can run."
