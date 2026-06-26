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

    // static site (feed.xml content-type is set via site/_headers — the Worker
    // does not run for paths that match a static asset)
    return env.ASSETS.fetch(request);
  },
};
