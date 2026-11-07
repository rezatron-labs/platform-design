# Changelog

Notable changes to the design language. The reasoning behind each decision lives
in [GUIDE.md](GUIDE.md); this is the short version, with the compatibility impact.

Class names and token names are public API — see GUIDE.md Part 6. CSS has no
compiler, so a rename that would be a caught build error in Java is a silently
unstyled control here. Renames are major. Nothing is deleted in a minor.

## v0.4.0 — 2026-11-06

Out of Money Manager's Bill-pay redesign, which lays a theme over the language:
its own palette and type, with the spacing, radii, control heights, focus width,
motion and states kept. These are five things a theme cannot reach, fixed here
rather than worked around in the app. Nothing is renamed or removed, so an app
on `v0.3.0` upgrades by changing the tag. One fix changes what renders: a
field's size (see Compatibility).

**Added**

- `--rz-focus`: the focus ring's colour, `var(--rz-accent)` in the light block
  and in both dark blocks. Every focus outline in `controls.css`, and the
  focused field's border, now read it instead of the accent. A theme whose
  accent is not a hue (Money Manager's primary button is ink) maps it to a
  colour of its own. It does so in each of its three blocks, because the dark
  blocks restate the default and their selectors outrank a bare `:root`.
- `.rz-table--controls`: every body row is 40px from rule to rule, which seats
  a 32px control with 4px above and below. Rows with and without a control
  line up.
- `.rz-table--reading`: a ruled reading table. Headers are set as words
  (`--rz-text-small`, sentence case, no tracking), every row is ruled off
  including the last, and cells are inset at both ends. Composes with
  `--controls`. Not named `--ruled`, which stays free for rules between columns.
- `.rz-btn--danger-quiet`: critical ink and no fill, the critical tint on
  hover, one step past it when pressed, and the standard disabled swap. It is
  for a destructive action that sits beside content. The filled `--danger`
  stays for a dialog that exists only to confirm a deletion.
- `.rz-btn--danger-outlined`: the quiet danger button with a critical border.
  It is for the destructive choice in an inline confirmation, beside a safer
  one such as Keep it.
- `.rz-badge__icon`: a 1em square slot for a badge's glyph or inline SVG, in
  the label's colour, so stacked badges start their labels on one line.
- `contrast.py` resolves `var(--rz-…)` aliases per theme, and reads a
  `color-mix()` fill out of `controls.css` by its selector rather than
  restating it. It holds the focus ring to 3:1 on the surface and the ground.
  It holds the quiet danger button's ink to 4.5:1 on both at rest, on its hover
  tint and on its pressed mix, and the outlined button's border to 3:1 on both.
- `preview.html` shows each change in both themes: an input, a select and a
  button at one height; the ring keeping its colour in a region whose accent is
  ink; the three volumes of danger button side by side, disabled, and in an
  inline confirmation; stacked badges with icons; and the two table variants,
  alone and together.

**Fixed**

- `.rz-field` is `box-sizing: border-box`. An input took its padding and border
  on top of its height and width, so it was 34px tall beside 32px buttons and
  selects, and 18px wider than the container `width: 100%` told it to fill.
- `.rz-table-wrap` takes the focus ring when it is made focusable. A table that
  scrolls sideways and holds nothing focusable needs its wrap to have
  `tabindex="0"`, `role="region"` and a name so a keyboard can scroll it, and
  until now that wrap drew the browser's ring rather than the language's.
  `controls.css` and the reading-table specimen show the markup.

**Compatibility**

Minor. Six additions and two fixes, with no rename, no removal, and no
existing token changing value.

- `--rz-focus` defaults to the accent in every block, so every focus ring
  renders as it did on `v0.3.0`.
- `.rz-field` changes size. An input is now 32px tall (it was 34px) and exactly
  as wide as its container (it was 18px wider). Selects already measured this
  way. A `box-sizing: border-box` an app added locally as a workaround is now
  redundant and harmless. A width an app shortened by hand to stop the overflow
  is now 18px narrower than it needs to be.
- The new classes change nothing until markup uses them.

## v0.3.0 — 2026-09-10

Out of Money Manager's 401(k) history chart, the first chart to need a data
series that is not a status. Additive only: one token added, nothing renamed,
nothing removed, so an app on `v0.2.0` upgrades by changing the tag and nothing
else.

**Added**

- `--rz-series-1` — the first non-status chart series: `#5a86d6` in light and
  `#5b82d0` in dark, defined in the light block and in both dark blocks. A chart
  that sets a quantity beside a gain and a loss needs a colour that reads as
  neither. The accent does not separate from `--rz-good` — ΔE 14.7 in light and
  13.8 in dark, under the normal-vision floor of 15 in both themes — while this
  slot's worst neighbour is ΔE 20.3 in light and 20.1 in dark. GUIDE Part 3
  records what it was validated against.
- `contrast.py` holds it to 3:1 against the surface and the ground in each theme,
  and `preview.html` shows it standing beside `--rz-good` and `--rz-warn`.

**Compatibility**

Minor. One additive token, no rename, no removal, and no existing token changes
value, so every `v0.2.0` screen renders identically.

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
