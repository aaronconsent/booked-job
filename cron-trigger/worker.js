// Cloudflare Cron Trigger — reliably fires the booked-job GitHub Actions workflow.
// Replaces GitHub's flaky internal cron (which dropped ~60% of scheduled runs and
// skipped the nightly force push). Cloudflare cron triggers are reliable + free.
//
// Triggers (see wrangler.toml):
//   "5 * * * *"  -> hourly automation run
//   "23 2 * * *" -> 02:23 UTC = 9:23 PM CDT nightly FORCE push (force=true)
//
// Requires one secret: GITHUB_DISPATCH_TOKEN — a GitHub fine-grained PAT scoped to
// the booked-job repo with **Actions: Read and write**.

const REPO = "aaronconsent/booked-job";
const WORKFLOW = "automation.yml";
const FORCE_CRON = "23 2 * * *";

export default {
  async scheduled(event, env, ctx) {
    const force = event.cron === FORCE_CRON;
    const res = await fetch(
      `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_DISPATCH_TOKEN}`,
          Accept: "application/vnd.github+json",
          "User-Agent": "booked-job-cron",
          "Content-Type": "application/json",
          "X-GitHub-Api-Version": "2022-11-28",
        },
        body: JSON.stringify({ ref: "main", inputs: { force } }),
      }
    );
    if (!res.ok) {
      console.log(`dispatch FAILED ${res.status}: ${await res.text()}`);
    } else {
      console.log(`dispatched ${force ? "FORCE" : "hourly"} run`);
    }
  },
};
