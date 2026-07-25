DRAFT ONLY — not sent. Review, edit, and send yourself from your own email.

To: adr@adrindia.org
(Decoded from the Cloudflare-obfuscated mailto link on https://adrindia.org/content/faqs,
under "If you... want to discuss using MyNeta for research... please write to us at")

Subject: Research/civic-tech use of MyNeta data — Halka, a voter information tool

---

Hello,

I'm building Halka, a free, non-commercial voter information tool that helps
Indian voters see candidates' ECI-declared affidavit details — criminal
cases, assets, education, profession — for their own constituency before an
election, sourced and cited the way MyNeta itself presents it.

I'd like to pull structured data from MyNeta (candidate lists and individual
affidavit pages) programmatically, starting with constituencies in active
nomination windows and expanding over time, rather than by hand per seat. A
few specifics, in case they're useful on your end:

- Purpose: voter education, non-commercial, no ads, no resale of data —
  consistent with the non-commercial terms on your FAQ page.
- Volume/pace: rate-limited (currently ~1 request per 1–3 seconds), starting
  with single constituencies and states, not a full-archive crawl.
- Attribution: every data point in Halka carries its source URL back to the
  specific MyNeta page it came from, visible in the product itself.
- I noticed your FAQ mentions API access for media houses — if that's
  available more broadly for a non-commercial civic project like this, I'd
  much rather use that than scrape pages directly. Happy to share more about
  Halka if useful for that conversation.

Is this the kind of use your team is comfortable with, and is there a
preferred way (API, bulk export, or a scraping approach you'd recommend) for
a project like this to pull your data responsibly and at the pace you're
okay with?

Thank you for the work ADR/MyNeta does — it's the backbone of what I'm
trying to build.

[Your name]
[Your contact info]
[Link to the Halka prototype, if you want to include one]

---

NOTES FOR YOU (not part of the email):
- Fill in your name/contact before sending — left blank deliberately, I'm
  not putting placeholder identity details into an email sent under your
  name without you choosing them.
- Consider attaching or linking halka-prototype.html (or a hosted version)
  so ADR can see this is a real, working, source-citing tool and not a
  vague request.
- If you don't hear back in a couple of weeks, ADR's own FAQ still confirms
  non-commercial reuse is allowed without asking first — this email is about
  building a direct relationship and doing right by a nonprofit whose data
  this depends on, not a hard legal gate on using MyNeta at all.
