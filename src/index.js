/**
 * Booked Job Worker — serves the static site and handles email capture.
 * /api/subscribe (POST {email}) -> adds the contact to the Resend audience.
 * Everything else falls through to the static assets in /site.
 *
 * Worker secrets/vars (set in the Cloudflare dashboard):
 *   RESEND_API_KEY       (secret)
 *   RESEND_AUDIENCE_ID   (var)
 */
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/subscribe" && request.method === "POST") {
      try {
        const { email } = await request.json();
        if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
          return Response.json({ ok: false, error: "invalid email" }, { status: 400 });
        }
        if (!env.RESEND_API_KEY || !env.RESEND_AUDIENCE_ID) {
          // Not configured yet — accept gracefully so the form still works.
          return Response.json({ ok: true, pending: true });
        }
        const r = await fetch(
          `https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${env.RESEND_API_KEY}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ email, unsubscribed: false }),
          }
        );
        return Response.json({ ok: r.ok });
      } catch (e) {
        return Response.json({ ok: false }, { status: 500 });
      }
    }

    // Tracked funnel redirect to Consent Resolve (UTM-tagged) + KV click counter.
    if (url.pathname === "/cr") {
      if (env.CR_KV) {
        try { await env.CR_KV.put("clicks", String((parseInt(await env.CR_KV.get("clicks")) || 0) + 1)); } catch (e) {}
      }
      return Response.redirect("https://consentresolve.com/?utm_source=bookedjob&utm_medium=content&utm_campaign=funnel", 302);
    }
    if (url.pathname === "/cr/count") {
      let n = 0;
      if (env.CR_KV) { try { n = parseInt(await env.CR_KV.get("clicks")) || 0; } catch (e) {} }
      return Response.json({ clicks: n });
    }

    // ===== Bluesky custom feed generator ("Home-Service Talk") =====
    const OUR_DID = "did:plc:3ssakol7dqe4nnlgqwnrduxo";
    const FEED_URI = `at://${OUR_DID}/app.bsky.feed.generator/homeservice`;

    if (url.pathname === "/.well-known/did.json") {
      return Response.json({
        "@context": ["https://www.w3.org/ns/did/v1"],
        id: "did:web:booked-job.com",
        service: [{ id: "#bsky_fg", type: "BskyFeedGenerator", serviceEndpoint: "https://booked-job.com" }],
      });
    }
    if (url.pathname === "/xrpc/app.bsky.feed.describeFeedGenerator") {
      return Response.json({ did: "did:web:booked-job.com", feeds: [{ uri: FEED_URI }] });
    }
    if (url.pathname === "/xrpc/app.bsky.feed.getFeedSkeleton") {
      // Feed skeleton is precomputed by scripts/bluesky_feed_refresh.py (authenticated
      // search, a few times/day) and served as a static asset.
      const limit = Math.min(parseInt(url.searchParams.get("limit") || "30", 10) || 30, 50);
      try {
        const r = await env.ASSETS.fetch(new URL("/feedskel.json", request.url));
        const d = await r.json();
        return Response.json({ feed: (d.feed || []).slice(0, limit) });
      } catch (e) {
        return Response.json({ feed: [] });
      }
    }

    // static site (feed.xml content-type is set via site/_headers — the Worker
    // does not run for paths that match a static asset)
    return env.ASSETS.fetch(request);
  },
};
