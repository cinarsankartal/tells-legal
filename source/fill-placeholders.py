#!/usr/bin/env python3
"""
Fills the placeholders in the legal templates and writes the result to legal/dist/.

    python3 legal/fill-placeholders.py

The templates in legal/ are never modified — edit VALUES below, re-run, and
publish whatever lands in legal/dist/. Re-running is safe and idempotent.

All values below were supplied and confirmed by the owner on 2026-08-17.

The output is four complete, self-contained HTML pages, published through GitHub
Pages, plus a plain-text copy of the terms for App Store Connect:

    privacy-policy.html     linked from the app and from App Store Connect
    terms-of-use.html       linked from the app; also the custom EULA
    support.html            App Store Connect's Support URL
    index.html              optional, stops the folder URL 404ing
    terms-of-use.txt        paste into the custom EULA field

The filenames and their being in the SAME directory matter: the pages link to
each other by relative path, so renaming or separating them breaks a link
somewhere else. Everything else is inside the files — no CSS, fonts, images or
scripts are fetched from anywhere.

PUBLISH legal/dist/, NEVER legal/. The templates here still contain [EMAIL] and
friends plus the editorial comments; pushing one by mistake put a support page
live reading "[EMAIL]" in four places.

Section 6 of the privacy policy describes GitHub Pages specifically. Moving the
pages to different hosting means rewriting it; see the LOG_RETENTION note below.
"""

import re
import sys
from html import unescape as html_unescape
from pathlib import Path

# ---------------------------------------------------------------------------
# EDIT THESE
# ---------------------------------------------------------------------------

VALUES = {
    # The day you publish this version. Changes every time you revise the text.
    # Shown as "Last updated", so it must be the day the set actually goes up
    # and never a day in the future. Moved from 21 August to 14 September when
    # support.html joined the set: that page did not exist in August, and a page
    # created today carrying an August date is exactly the sort of small untruth
    # a document like this cannot afford.
    "DATE": "24 September 2026",

    # The party responsible.
    #
    # As of 2026-09-14 there is no registered business at all — the şahıs
    # şirketi is planned, not filed. That changes nothing here, and nothing in
    # the published documents: both name a natural person at an address, which
    # is true either way, and neither claims a registration. Copyright in the
    # app vests in its author automatically, with no filing required.
    #
    # It does bear on the DSA trader declaration and on the day any money
    # changes hands. See the note under EMAIL's sibling values and the project
    # notes; in short, free-and-unregistered is the one combination where
    # "non-trader" is arguable, and registering or monetising ends that.
    #
    # When the şahıs şirketi is filed, the name below stays the same: a sole
    # proprietorship has no separate legal entity, so the controller remains the
    # natural person under their own full name. Two consequences worth holding
    # on to —
    #
    #   1. This name is published on the open internet, and so is the address
    #      below. See the note there.
    #   2. Liability is personal and unlimited. There is no company standing
    #      between a claim and you, which is why sections 10 to 12 of the Terms
    #      are worth keeping intact.
    #
    # If this is later incorporated, replace this with the registered company
    # name — the surrounding wording works for either.
    "COMPANY": "Çınar Şan Kartal",

    # The registered address, published on the open internet next to a real
    # person's full name.
    #
    # This is the owner's home address, and that is a deliberate decision taken
    # on 2026-08-17 with the alternative on the table: a virtual office (sanal
    # ofis) is a valid registered address, costs very little, and would have
    # kept a home address off the internet. It was declined. Nothing in these
    # documents mitigates it, so if the app gets traction and the wrong kind of
    # attention with it, moving to a virtual office is the only lever left —
    # change it here and re-publish both pages.
    #
    # The documents append ", Türkiye" after it, so don't add a country here.
    "ADDRESS": "Esatpaşa Mah. Güzel Bahar Sok. No: 4A, Daire 17, 34704 Ataşehir/İstanbul",

    # Must be a working inbox that you actually read. App Review does email it,
    # and it must match Links.support in SettingsView.swift.
    #
    # This is published on the open web, so it will be scraped and it will get
    # spam. A dedicated address rather than a personal one, which is the right
    # call — move it to the app's own domain when there is one, and change it
    # here and in Links.support at the same time.
    "EMAIL": "vibecheckappsupport@gmail.com",

    # Courts with jurisdiction — normally where the entity is registered.
    #
    # Ataşehir is on the Anatolian side, and there is no separate Ataşehir
    # courthouse: cases for companies there go to the İstanbul Anadolu courts
    # (İstanbul Anadolu Adalet Sarayı, Kartal). "İstanbul Anadolu" is the
    # designation a Turkish court would recognise; "İstanbul (Ataşehir)" is not.
    "CITY": "İstanbul Anadolu",

    # Symbolic cap for a free app. Consumer law may override it for consumers
    # in Türkiye and the EU, which is why the savings clause in section 11 is
    # there. Keep it small and honest rather than aggressive.
    "LIABILITY_CAP": "2.000 TRY",

    # How long you keep support emails before deleting them.
    "SUPPORT_RETENTION": "12 months",
}

# THERE IS DELIBERATELY NO LOG_RETENTION. It has been added and removed twice;
# read this before adding it a third time.
#
# The value only makes sense when *you* hold the access logs, and that depends
# entirely on who hosts the pages:
#
#   Google Sites  — logs are Google's, plus a Google cookie (NID). No promise
#                   could be made on Google's behalf. Key absent.
#   Own server    — logs are yours. Key present, 30 days.
#   GitHub Pages  — where we are now. GitHub Pages gives the site's author no
#                   access logs and no visitor analytics at all, so there is
#                   nothing for you to retain and nothing to promise. GitHub
#                   logs for its own purposes under its own privacy statement.
#                   Key absent.
#
# So: add this key back only if the pages move to hosting whose logs you can
# actually read and delete. If they do, section 6 of the privacy policy has to
# be rewritten at the same time — it currently states in plain terms that we
# receive no record of your visit, which would become false.

# ---------------------------------------------------------------------------

TEMPLATES = ["privacy-policy.html", "terms-of-use.html", "support.html", "index.html"]

# App Store Connect's custom EULA field takes plain text, not HTML. Generating
# it from the same source as the published page is the whole point: an EULA that
# says something different from the terms the app links to is worse than not
# having a custom one at all.
PLAIN_TEXT = {"terms-of-use.html": "terms-of-use.txt"}

# index.html is optional and nothing links to it — it only stops the folder URL
# itself returning a 404. It must go in the same subfolder as the two documents.
# Dropping it at the root of a Pages repo that already has a homepage replaces
# that homepage, which is why the script warns about it on every run.
OPTIONAL = {"index.html"}

# support.html is what goes in App Store Connect's Support URL field, which
# will not accept a mailto: address. A reviewer clicks it, so its answers have
# to match the app — it is generated from the same values for that reason.

# Values that are still invented samples. Once a placeholder is filled, the
# leftover scan can't catch it any more — a made-up company name reads exactly
# like a real one — so these are tracked by hand. Add a key here while its value
# is still a guess, and remove it once the value is true.
#
# Currently empty: every value above was supplied by the owner rather than
# invented here.
STILL_EXAMPLE: dict[str, str] = {}

# Supplied, but not yet final. The script nags about exactly these on every run.
#
# Now empty: every value above was confirmed by the owner on 2026-08-17 —
# COMPANY, ADDRESS and CITY (şahıs şirketi under their own name, at their home
# address), EMAIL (the app's own support mailbox) and DATE (13 August 2026,
# fixed as the version date rather than the upload date).
#
# Put a key back in here if a value goes soft again — a pending move to a
# virtual office, a domain change, a revision that needs a new date.
PROVISIONAL_KEYS: set[str] = set()

# Matches [NAME] and also [NAME, e.g. something] so the inline hints get
# replaced along with the token.
def token_pattern(name: str) -> re.Pattern:
    return re.compile(r"\[" + re.escape(name) + r"(?:,[^\]]*)?\]")


def to_plain_text(html: str) -> str:
    """Flatten the document to plain text for the App Store Connect EULA field.

    Paragraphs are kept on one line each rather than hard-wrapped, because the
    field reflows them; hard wraps would show up as ragged breaks.
    """
    text = html.split("<body>", 1)[1].split("</body>", 1)[0]

    # Drop the footer — it is navigation between the two published pages and
    # means nothing in a pasted EULA.
    text = re.sub(r"<footer>.*?</footer>", "", text, flags=re.DOTALL)

    # Links become "text (url)", except mailto: and same-page links where the
    # visible text already is the address or the title.
    def link(m: re.Match) -> str:
        href, label = m.group(1), m.group(2)
        if href.startswith("mailto:") or href.endswith(".html"):
            return label
        return f"{label} ({href})"

    text = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', link, text, flags=re.DOTALL)

    # Section numbers sit in their own span and need a separator, or "11" and
    # "Limitation of liability" run together.
    text = re.sub(r'<span class="n">(\d+)</span>', r"\1. ", text)

    text = re.sub(r"<li>", "\n  - ", text)
    text = re.sub(r"<br\s*/?>", "\n", text)

    # Headings and paragraphs become blank-line-separated blocks.
    text = re.sub(r"</(h1|h2|h3|p|ul|ol|div|header)>", "\n\n", text)
    text = re.sub(r"<(h1|h2|h3)[^>]*>", "\n\n", text)

    text = re.sub(r"<[^>]+>", "", text)

    text = html_unescape(text)

    # Collapse the whitespace the markup left behind: spaces before punctuation,
    # runs of blank lines, trailing spaces.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def main() -> int:
    here = Path(__file__).resolve().parent
    out_dir = here / "dist"
    out_dir.mkdir(exist_ok=True)

    problems = []

    for filename in TEMPLATES:
        source = here / filename
        if not source.exists():
            problems.append(f"missing template: {filename}")
            continue

        text = source.read_text(encoding="utf-8")

        # The "placeholders to replace" note is scaffolding for whoever fills
        # the template in. It must not survive into the published page.
        text = re.sub(
            r"\s*<p><strong>Placeholders to replace before publishing:.*?</p>",
            "",
            text,
            flags=re.DOTALL,
        )

        # Same for the editorial comment block at the top.
        text = re.sub(r"^\s*<!--.*?-->\s*", "", text, count=1, flags=re.DOTALL)

        for name, value in VALUES.items():
            text = token_pattern(name).sub(value, text)

        # Anything still in brackets means a placeholder was missed. The
        # editorial comments at the top of each template talk *about*
        # placeholders, so they're excluded from the scan.
        body = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        leftovers = sorted(set(re.findall(r"\[[A-Z_]{3,}[^\]]*\]", body)))
        if leftovers:
            problems.append(f"{filename}: unfilled {', '.join(leftovers)}")

        # These pages are uploaded to a web server as standalone documents, so
        # they have to BE standalone documents. The charset line is the one that
        # matters most and fails most quietly: without it a server that doesn't
        # send charset in the Content-Type header leaves a browser to guess, and
        # "Çınar Şan Kartal" in the controller's name renders as mojibake — in
        # the one paragraph of a privacy policy that has to be exactly right.
        required = {
            "<!DOCTYPE html>": "doctype (without it browsers use quirks mode)",
            '<meta charset="utf-8">': "charset (Turkish characters break without it)",
            "<html lang=": "lang attribute",
            "<body>": "body element",
        }
        for needle, why in required.items():
            if needle not in text:
                problems.append(f"{filename}: missing {why}")

        (out_dir / filename).write_text(text, encoding="utf-8")
        suffix = "   (optional)" if filename in OPTIONAL else ""
        print(f"wrote legal/dist/{filename}{suffix}")

        if filename in PLAIN_TEXT:
            plain = to_plain_text(text)
            (out_dir / PLAIN_TEXT[filename]).write_text(plain, encoding="utf-8")
            print(f"wrote legal/dist/{PLAIN_TEXT[filename]}   "
                  f"({len(plain):,} chars, paste into App Store Connect)")

    # GitHub Pages runs Jekyll over a repo unless this file is present. Nothing
    # in these documents is Liquid syntax, so Jekyll would pass them through
    # unchanged today — but the build step is a moving part that can only ever
    # do harm here, and it costs one empty file to switch it off.
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    print("wrote legal/dist/.nojekyll   (repo root, turns off Jekyll)")

    if problems:
        print("\nNot done yet:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    unchanged = [key for key, sample in STILL_EXAMPLE.items() if VALUES.get(key) == sample]

    if unchanged:
        print("\n  DO NOT PUBLISH YET — these are still the invented samples:")
        for key in unchanged:
            print(f"    {key:<18} {VALUES[key]}")
        print("\n  A made-up company name and address in a published privacy")
        print("  policy is worse than a visible [PLACEHOLDER], because nothing")
        print("  about it looks wrong. Replace them, then re-run.")
        return 2

    provisional = [key for key in VALUES if key in PROVISIONAL_KEYS]

    if provisional:
        print("\n  CHECK BEFORE PUBLISHING — not confirmed final:")
        for key in provisional:
            print(f"    {key:<10} {VALUES[key]}")
        print("\n  DATE must be the day these pages actually go up. Set it, re-run,")
        print("  and publish the same day — then empty PROVISIONAL_KEYS.")

    print("\n  index.html is OPTIONAL. It goes in the same subfolder as the two")
    print("  documents. Do NOT put it at the root of a Pages repo that already")
    print("  has a homepage — it would replace it.")

    print("\nCommit the documents to the GitHub Pages repo, in the same directory,")
    print("under exactly these names. Then point Links in SettingsView.swift at")
    print("the published URLs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
