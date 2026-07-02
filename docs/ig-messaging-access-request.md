# Instagram Messaging (DM inbox) — Advanced Access Request

Unlocks reading Instagram DMs via the Graph API so `ig_dm_inbox.py` can surface leads
to a human inbox. Same App-Review path as the insights permission (already granted).
The `(#3) Application does not have the capability` error = this hasn't been approved yet.

## Prereqs (already true for Booked Job)
- Meta app `4272691649710635`, published/Live.
- IG professional account (`bookedjob`) linked to the FB Page, System User token in `secrets/fb.env`.

## Permission to request
- **`instagram_manage_messages`** — Advanced Access (App Review).

## Where
developers.facebook.com → app `4272691649710635` → **App Review → Permissions and
Features** → search **`instagram_manage_messages`** → **Request Advanced Access**.

## Use-case blurb (paste)
> Booked Job uses the Instagram Graph API to read incoming direct messages **on our
> own single Instagram professional account** and surface them to an internal inbox
> so our team can reply by hand to genuine customer inquiries (contractors asking
> about our marketing content). We do **not** auto-message strangers, do not bulk-DM,
> and do not redistribute message data — it's a first-party, human-in-the-loop inbox
> for one owned account. Our app already holds `instagram_manage_insights` for the
> same account.

## Requirements Meta will ask for
- **Business Verification** (likely already done for the insights grant).
- A short **screencast** showing the inbox use (I can script it).
- Confirmation it's first-party (one owned account).

## Screencast script (Meta requires a short video — ~60s)
Record your screen showing this exact flow:
1. Open the Booked Job Instagram professional account → **Inbox/DMs**. Show a real incoming DM.
2. Cut to your app/tool (the terminal running `python3 scripts/ig_dm_inbox.py`, or the
   dashboard) → show the DM pulled into `content/ig_dm_inbox.md` — "we read our own
   account's DMs into an internal inbox."
3. Show a **human** typing a reply back in the Instagram app (not automated).
4. Narrate: *"We use instagram_manage_messages to read incoming DMs on our own single
   business account into a private inbox so our team replies by hand. No automation to
   strangers, no bulk messaging, one owned account."*

## After approval
`ig_dm_inbox.py` (already built + wired into run_all) auto-detects access and starts
filling `content/ig_dm_inbox.md`. Nothing else to change.
