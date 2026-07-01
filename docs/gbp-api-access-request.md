# Google Business Profile API — Access Request (Local Posts)

**Goal:** raise the Business Profile API quota from 0 → 300 QPM, which unlocks the
restricted resources including **Local Posts** (Google Posts) so Booked Job can
auto-publish update posts to its own profile.

## Before you submit — eligibility check
- [ ] The Booked Job GBP is **verified** (not just claimed) and **active 60+ days**.
      *(If it's still "pending verification," finish that first — the request needs a verified profile.)*
- [x] Business has a website: https://booked-job.com
- [x] Google Cloud project already exists (shared with YouTube/Blogger): **project number `848808722082`**

## Where to submit
Form: **https://support.google.com/business/contact/api_default**
Dropdown: **"Application for Basic API Access"**

## Field values (paste)
| Field | Value |
|---|---|
| Google Cloud **Project number** | `848808722082` |
| **Contact email** | *(the email that is an **Owner** on the Booked Job Google Business Profile)* |
| **Business name** | Booked Job |
| **Business website** | https://booked-job.com |

## Use-case description (paste into the justification box)
> Booked Job operates a single, first-party Google Business Profile for our own
> verified business (booked-job.com). We are requesting Business Profile API access
> to programmatically manage **only our own profile**:
>
> 1. Publish regular **Local Posts** (update / what's-new posts) — marketing content
>    and practical tips for our audience of home-service contractors.
> 2. Keep our **business information** (hours, description, categories, photos) in
>    sync with our website.
> 3. **Read and respond to customer reviews** promptly.
>
> This is a first-party integration for a **single owned location** — no third-party
> businesses, no reselling or redistribution of API data, and low request volume
> (well under standard quotas). Our Google Cloud project (848808722082) already
> powers our YouTube and Blogger integrations for the same brand. We will comply
> with the Business Profile API Policies and Google's User Data Policy.

## After approval
- Check quota in Cloud Console: **0 QPM = pending, 300 QPM = approved.**
- Then run `python3 scripts/gbp_oauth.py` (already built) to connect, and I'll wire the poster.
