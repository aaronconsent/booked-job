/**
 * Booked Job Worker — serves the static site and handles email capture.
 * /api/subscribe (POST {email}) -> adds the contact to the Resend audience.
 * Everything else falls through to the static assets in /site.
 *
 * Worker secrets/vars (set in the Cloudflare dashboard):
 *   RESEND_API_KEY       (secret)
 *   RESEND_AUDIENCE_ID   (var)
 */
const WELCOME_HTML = `<div style="font:16px/1.6 -apple-system,system-ui,sans-serif;color:#1a1a1a;max-width:560px;margin:0 auto">
<p>You're in. As promised — the numbers most marketers won't put in front of you, on one page:</p>
<h3 style="margin:22px 0 6px">💸 What a booked job actually costs</h3>
<p style="margin:0">Angi ≈ <b>$542</b> · Thumbtack ≈ <b>$250</b> · Google Local Service Ads ≈ <b>$168</b> — <i>per booked job</i>, after close rates. Cost per <i>lead</i> is the number that lies to you.</p>
<h3 style="margin:22px 0 6px">⭐ Reviews decide the call before it happens</h3>
<p style="margin:0"><b>91%</b> of homeowners won't consider a shop under 4 stars. Topping a competitive HVAC market takes ~<b>519</b> reviews; the median map-pack plumber has ~<b>337</b>.</p>
<h3 style="margin:22px 0 6px">📞 Speed beats budget</h3>
<p style="margin:0"><b>78%</b> hire whoever answers first. Responding in 5 minutes vs 30 is up to <b>100×</b> more likely to connect — and the average shop misses <b>14%</b> of its calls.</p>
<h3 style="margin:22px 0 6px">🖥️ Your website</h3>
<p style="margin:0">About <b>98%</b> of visitors leave without calling. Phone number up top, proof on page one, load under 3 seconds. That's most of it.</p>
<p style="margin:24px 0 6px">Run <i>your</i> numbers with the free calculators:</p>
<p style="margin:0">→ <a href="https://booked-job.com/tools/cost-per-booked-job-calculator/">Cost per booked job</a><br>
→ <a href="https://booked-job.com/tools/google-review-calculator/">Reviews you need to rank</a><br>
→ <a href="https://booked-job.com/tools/job-pricing-calculator/">Price a job for margin</a></p>
<p style="margin:24px 0 4px">One favor: <b>hit reply and tell me your trade</b> — it shapes what I send next.</p>
<p style="margin:0">— Aaron, Booked Job<br><span style="color:#888;font-size:13px">Get found. Get picked. Get booked. · Unsubscribe anytime.</span></p>
</div>`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // canonical host: 301 www -> apex (SEO — one URL per page)
    if (url.hostname === "www.booked-job.com") {
      url.hostname = "booked-job.com";
      return Response.redirect(url.toString(), 301);
    }

    if (url.pathname === "/api/subscribe" && request.method === "POST") {
      try {
        const body = await request.json();
        const email = body.email;
        const source = (body.source || "").toString().slice(0, 120);
        if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
          return Response.json({ ok: false, error: "invalid email" }, { status: 400 });
        }
        if (!env.RESEND_API_KEY || !env.RESEND_AUDIENCE_ID) {
          return Response.json({ ok: true, pending: true });
        }
        const r = await fetch(
          `https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts`,
          { method: "POST", headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
            body: JSON.stringify({ email, unsubscribed: false }) }
        );
        if (r.ok) {
          // instant welcome — deliver the promised cheat sheet + hook the ICP (best-effort)
          try {
            await fetch("https://api.resend.com/emails", {
              method: "POST",
              headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
              body: JSON.stringify({ from: "Booked Job <newsletter@booked-job.com>", to: [email],
                reply_to: "hello@booked-job.com", subject: "The honest contractor-marketing math (as promised) 🛠️", html: WELCOME_HTML }),
            });
          } catch (e) {}
          // track signups + which page converts (for optimization toward the goal)
          if (env.CR_KV) {
            try {
              await env.CR_KV.put("signups", String((parseInt(await env.CR_KV.get("signups")) || 0) + 1));
              if (source) { const m = JSON.parse(await env.CR_KV.get("signup_src") || "{}"); m[source] = (m[source] || 0) + 1; await env.CR_KV.put("signup_src", JSON.stringify(m)); }
            } catch (e) {}
          }
        }
        return Response.json({ ok: r.ok });
      } catch (e) {
        return Response.json({ ok: false }, { status: 500 });
      }
    }
    // signup metrics for the dashboard (which pages convert)
    if (url.pathname === "/ops/signups") {
      let total = 0, src = {};
      if (env.CR_KV) { try { total = parseInt(await env.CR_KV.get("signups")) || 0; src = JSON.parse(await env.CR_KV.get("signup_src") || "{}"); } catch (e) {} }
      return Response.json({ total, by_source: src });
    }

    // Pipeline inbox reader — outreach replies captured by the email() handler below.
    // Gated by the INBOX_KEY worker secret; ?since=ISO returns only newer messages.
    if (url.pathname === "/ops/inbox") {
      if (!env.INBOX_KEY || url.searchParams.get("key") !== env.INBOX_KEY) {
        return Response.json({ error: "forbidden" }, { status: 403 });
      }
      let msgs = [];
      if (env.CR_KV) { try { msgs = JSON.parse(await env.CR_KV.get("inbox") || "[]"); } catch (e) {} }
      const since = url.searchParams.get("since");
      if (since) msgs = msgs.filter((m) => m.ts > since);
      return Response.json({ messages: msgs, count: msgs.length });
    }

    // Durable KV get/set for pipeline secrets that rotate (e.g. Tumblr's refresh token,
    // which changes every use — ephemeral CI runners can't persist it any other way).
    // Gated by INBOX_KEY. GET ?key=&k=<kvkey> returns the value; POST body sets it.
    if (url.pathname === "/ops/kv") {
      if (!env.INBOX_KEY || url.searchParams.get("key") !== env.INBOX_KEY) {
        return Response.json({ error: "forbidden" }, { status: 403 });
      }
      const k = url.searchParams.get("k");
      if (!k || !env.CR_KV) return Response.json({ error: "bad request" }, { status: 400 });
      if (request.method === "POST") {
        const v = await request.text();
        await env.CR_KV.put(k, v);
        return Response.json({ ok: true });
      }
      const val = await env.CR_KV.get(k);
      return Response.json({ value: val }, { headers: { "Cache-Control": "no-store" } });
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

    // ===== Daily manual-task done-state + grades (KV) =====
    if (url.pathname === "/tasks/state") {
      const date = url.searchParams.get("date") || "";
      let daily = [], setup = [], roster = [], grades = {};
      if (env.CR_KV) {
        try { daily = JSON.parse(await env.CR_KV.get("td:" + date) || "[]"); } catch (e) {}
        try { setup = JSON.parse(await env.CR_KV.get("tsetup") || "[]"); } catch (e) {}
        try { roster = JSON.parse(await env.CR_KV.get("troster") || "[]"); } catch (e) {}
        try { grades = JSON.parse(await env.CR_KV.get("tg") || "{}"); } catch (e) {}
      }
      const vals = Object.values(grades);
      const running = vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
      return Response.json({ daily, setup, roster, grades, running, days: vals.length });
    }
    if (url.pathname === "/tasks/toggle" && request.method === "POST") {
      if (!env.CR_KV) return Response.json({ error: "no kv" }, { status: 500 });
      let body; try { body = await request.json(); } catch (e) { return Response.json({ error: "bad" }, { status: 400 }); }
      const { date, id, total, kind } = body;
      if (kind === "setup" || kind === "roster") {
        const key = kind === "roster" ? "troster" : "tsetup";
        let s = JSON.parse(await env.CR_KV.get(key) || "[]");
        s = s.includes(id) ? s.filter(x => x !== id) : [...s, id];
        await env.CR_KV.put(key, JSON.stringify(s));
        return Response.json({ [kind]: s });
      }
      let done = JSON.parse(await env.CR_KV.get("td:" + date) || "[]");
      done = done.includes(id) ? done.filter(x => x !== id) : [...done, id];
      await env.CR_KV.put("td:" + date, JSON.stringify(done));
      const pct = total ? Math.round(100 * done.length / total) : 0;
      let grades = JSON.parse(await env.CR_KV.get("tg") || "{}");
      grades[date] = pct;
      const keys = Object.keys(grades).sort().slice(-60);
      const capped = {}; keys.forEach(k => capped[k] = grades[k]);
      await env.CR_KV.put("tg", JSON.stringify(capped));
      const vals = Object.values(capped);
      const running = vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
      return Response.json({ done, pct, running, days: vals.length });
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

  // Inbound email (Cloudflare Email Routing -> "Send to Worker"): capture the
  // message in KV for the pipeline (outreach replies -> founder digest), then
  // forward the original to Aaron's inbox as before. Keeps the last 100.
  async email(message, env) {
    try {
      let raw = "";
      try {
        const buf = await new Response(message.raw).arrayBuffer();
        raw = new TextDecoder("utf-8", { fatal: false }).decode(buf.slice(0, 20000));
      } catch (e) {}
      const msg = {
        ts: new Date().toISOString(),
        from: message.from,
        to: message.to,
        subject: message.headers.get("subject") || "(no subject)",
        raw_head: raw,
      };
      if (env.CR_KV) {
        let inbox = [];
        try { inbox = JSON.parse(await env.CR_KV.get("inbox") || "[]"); } catch (e) {}
        inbox.unshift(msg);
        await env.CR_KV.put("inbox", JSON.stringify(inbox.slice(0, 100)));
      }
    } catch (e) {}
    await message.forward("hello@aaron.chat");
  },
};
