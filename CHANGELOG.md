# Changelog

Notable changes to the design language. The reasoning behind each decision lives
in [GUIDE.md](GUIDE.md); this is the short version, with the compatibility impact.

Class names and token names are public API — see GUIDE.md Part 6. CSS has no
compiler, so a rename that would be a caught build error in Java is a silently
unstyled control here. Renames are major. Nothing is deleted in a minor.

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
