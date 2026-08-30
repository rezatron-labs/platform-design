# Changelog

Notable changes to the design language. The reasoning behind each decision lives
in [GUIDE.md](GUIDE.md); this is the short version, with the compatibility impact.

Class names and token names are public API — see GUIDE.md Part 6. CSS has no
compiler, so a rename that would be a caught build error in Java is a silently
unstyled control here. Renames are major. Nothing is deleted in a minor.

## v0.2.0 — 2026-08-30

Out of Money Manager's adoption — the first application ever to consume this
library. Everything here is a defect the design process did not catch and one
hour of real use did. Additive only: nothing renamed, nothing removed, so an app
on `v0.1.0` upgrades by changing the tag and nothing else.

**Added**

- `.rz-nav--horizontal` — the top-bar and bottom-bar arrangements. `controls.css`
  told the reader to arrange the nav parts "into a sidebar, a top bar or a bottom
  bar" three lines above hardcoding `flex-direction: column`, so two of the three
  were reachable only by overriding the library. The modifier also turns the
  brand's and the foot's separating rules with the axis.
- `.rz-nav--touch` — 44px nav items, via `--rz-control-h-lg`. `.rz-nav-item` took
  the 32px pointer height and had no alternative, which meant the bottom bar —
  the arrangement that exists because of phones — was the one place the library
  broke GUIDE Part 4's own touch-target commitment. `rz-btn--lg` has done this
  for buttons since v0.1.0; this is its navigation counterpart.

**Fixed**

- GUIDE.md D6 listed a navigation part called `nav-utility`. No such class has
  ever shipped; the part is `nav-foot`. Documentation only — no CSS was named
  `nav-utility`, so nothing that worked stops working.
- `preview.html` gains a bottom-bar specimen. The `nav-utility` drift survived
  review because the specimen page exercised only the sidebar, and the specimen
  page is the only mechanism in this repo that fails when a claim stops being
  true.

**Compatibility**

Minor. Three additive classes, one documentation correction, no rename and no
removal. `.rz-nav` keeps its column default, so every v0.1.0 usage renders
identically.

## v0.1.0 — 2026-08-30

First release. Nothing has adopted it yet.

**Added**

- `tokens.css` — Harbor (colour) and Almanac (character) as CSS custom
  properties, prefixed `--rz-`. Dark mode honours `.dark`, `[data-theme="dark"]`
  and `prefers-color-scheme`, so RTO's existing `ThemeService` keeps working
  untouched.
- `controls.css` — the tier-2 set: button, field, checkbox, table, badge, alert,
  card, empty state, skeleton, navigation parts. Classes prefixed `rz-`.
- `tailwind-bridge.css` — optional, RTO only. Feeds Tailwind v4's `@theme` from
  the tokens, which is what fixes the two-different-blues bug structurally rather
  than by find-and-replace.
- `contrast.py` — the accessibility checks GUIDE.md Part 4 commits to. Parses
  `tokens.css` rather than restating the palette, so it cannot pass while
  checking colours the library no longer ships.
- `preview.html` — specimen page that imports the real stylesheets, so it fails
  when they do.

**Known gaps, deliberate**

Menus, modals, sheets, toasts, calendar grids, gauges and charts are absent.
Nothing has yet established what shape they take — see GUIDE.md D6 before adding
one.

**Expected next**

`v0.2.0`, out of Money Manager's refactor. The first real integration is where a
design language finds out what it is missing, and none of this has met an
application yet.
