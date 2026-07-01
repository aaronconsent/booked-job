# booked-job-cron — reliable scheduler (Cloudflare Worker)

GitHub's scheduled cron dropped ~60% of hourly runs and skipped the nightly force
push. This Cloudflare Worker fires the workflow on schedule via `workflow_dispatch`
— Cloudflare cron triggers are reliable and free.

## Deploy (one-time, ~3 min)
1. **Create a GitHub token** — [github.com/settings/tokens](https://github.com/settings/personal-access-tokens/new)
   → Fine-grained PAT → Resource owner: your org → Repository: **booked-job** →
   Permissions → **Actions: Read and write** → generate + copy.
2. From this folder:
   ```
   cd cron-trigger
   npx wrangler secret put GITHUB_DISPATCH_TOKEN   # paste the PAT
   npx wrangler deploy
   ```
3. Done. Cloudflare now fires the workflow **hourly** + a **9:23 PM CDT force push**,
   reliably. Verify in the Cloudflare dashboard → Workers → booked-job-cron → Logs.

## Notes
- GitHub's own hourly cron stays in `automation.yml` as a harmless fallback (the
  `concurrency` group serializes overlaps; runs are idempotent/self-gating).
- The **force** trigger is owned solely by this Worker (the GitHub force cron was
  removed) so it can't double-fire.
- To change timing, edit `crons` in `wrangler.toml` and redeploy. If you change the
  force time, update `FORCE_CRON` in `worker.js` to match.
