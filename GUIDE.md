# The Rezatron design language

The decisions, and the reasoning that produced them.

This document is the source of truth. Where a rendered preview, a screenshot or a
memory disagrees with it, this wins. It ships in the same commit as `tokens.css`,
so the values below and the values in the code cannot drift apart without someone
doing it deliberately.

**On format:** the global engineering standards call for ADRs in `docs/adr/`,
Nygard style. Every decision below carries its context, the decision, and its
consequences — the ADR content in one document rather than eight files, because a
design language is read as a whole. Split it if that stops being true.

---

## What these apps are

> **One person, deciding something, with no one to ask.**

- RTO Tracker — do I need to go into the office tomorrow?
- Money Manager — can I afford this?
- Dinner planner — what am I cooking this week?

Single user. No collaboration, no audience, nothing being sold. A decision at the
end, and the interface's job is to make that decision cost less effort.

Every choice in this document answers to that sentence. When a future decision
doesn't trace back to it, that is the signal to stop and ask why you're making it.

An earlier draft of this said "one person reading dated numbers." That was too
narrow — it described the two apps that existed rather than the thing they have in
common, and a guide justified by dated numbers would have read as inapplicable the
first time someone opened it while building something else. **The purpose statement
has to be pitched at the level that survives the next app**, or the language gets
forked by someone who was right to think it didn't fit.

---

# Part 1 — The rules

The transferable part. If you remember nothing else, remember these.

### 1. A limited palette applied consistently beats a good palette applied loosely

RTO today has nine semantic colour tokens and **720 raw colour utilities against 31
token uses** — a 23:1 ratio. The tokens aren't a system being bypassed; they're a
rounding error. The result isn't ugly, it's *incoherent*: two different blues both
called primary, seven corner radii, six greys for text.

Consistency is not a tax you pay for beauty. It **is** most of what reads as
designed.

### 2. One scale per property, and no escape hatch

Every value traces to a token. The moment an app writes `z-[300]` or `py-[7px]`,
the system has a hole, and the next person widens it. RTO's five ad-hoc z-index
values are that process already underway.

### 3. Keep the scale small enough to memorise

A scale you have to look up is a scale you will guess at, and guessing is drift.
Nine spacing steps, five radii, four elevations, three ink levels. If a case seems
to need a tenth step, the usual answer is that a *different* token is missing —
see control heights below.

### 4. Colour is never the only channel

Meaning must survive without hue. This isn't a preference; it's arithmetic (Part 2,
D4). Icon plus label carries the meaning; colour reinforces it for the people who
can see it.

### 5. Composable states need different physical zones

If two states can be true at once, they must occupy different space: **outside**
the box, **on** the box, **inside** the box. Otherwise they collide, which is
exactly how RTO's calendar ended up rendering *today*, *selected* and *focused*
identically.

### 6. Density is a ratio, not a size

The interesting number is not "14px base," it's how much larger the answer is than
the evidence. Ours is roughly **32:12**. A ratio survives compression — you can
shrink a dense screen without leaving the system, because the relationship holds
even when the absolute sizes don't.

### 7. Personality lives in type and structure, not in the accent hue

Swapping navy for violet gets you a different stock palette, not a distinctive one.
What makes three unrelated apps look like siblings is the **structural signature** —
here, the hairline under every label. The signature also outlives the typeface: swap
the face and the apps still look like yours.

### 8. Focus rings are not optional

They are the only way a keyboard user knows where they are. Never remove one without
replacing it with something at least as visible. `outline: none` with no replacement
is a bug, not a style choice.

### 9. The less your tooling can check, the more naming is a contract

Delete a method from a shared JAR and the build fails at the exact line. Rename a CSS
class and the app builds, the tests pass, and a button silently renders unstyled —
which is Money Manager's `class="primary"` bug today, live on the main call to action
of two screens, reported by nothing. Class and token names are public API. See Part 6.

---

# Part 2 — The decisions

## D1 — The language ships as tokens plus a small control layer

**Context.** RTO is Tailwind v4. Money Manager is component-scoped SCSS with an empty
global stylesheet. A shared language has to survive that or it's two languages with
one name.

One hard constraint settles the substrate before taste enters: **Chart.js draws to
canvas and cannot read a CSS class** — only a resolved value via `getComputedStyle`.
So the tokens must be CSS custom properties. Not Sass variables, not utility class
names.

**Decision.** Ship `tokens.css` (values) and `controls.css` (the common controls) as
plain CSS. RTO keeps Tailwind **for layout and spacing only**, with its `@theme` fed
from our tokens so `bg-surface` and `var(--rz-surface)` are the same value by
construction. Money Manager consumes the same two files from its global layer.

**Rejected: converting Money Manager to Tailwind.** Not on cost — on merit. Utilities
in templates put the language in a thousand template strings, which is precisely the
disease RTO has. Converting MM to Tailwind would be converting it to RTO's actual
problem and calling it consistency.

**Rejected: converting RTO off Tailwind.** Weeks of work; the responsive layout
utilities are load-bearing; and RTO has exactly one spec file, so the refactor would
be unverifiable.

**Rejected: tokens only, each app keeping its own control styles.** That guarantees
identical *values* while permitting divergent *expression* — a button that's a utility
string in one app and a `.btn` rule in the other drifts in padding, hover and radius,
everything except the hex. That's a shared palette, and a palette is not a design
language.

**Consequences.** Two authoring idioms persist for layout, deliberately. The
*decisions* live in one place; the *arrangement* stays each app's business.

## D2 — Distributed as a public repo, consumed as a git dependency pinned to a tag

**Context.** Both apps are in `rezatron-labs`. Both frontend CI jobs run on
`ubuntu-latest`, which has no route to `nexus.home:8082`.

**Decision.** `rezatron-labs/platform-design`, public, consumed as:

```json
"@rezatron-labs/design": "github:rezatron-labs/platform-design#v0.1.0"
```

**Consequences.** Zero auth anywhere — no `.npmrc`, no PAT, no secret, and no change
to either app's existing CI. No build-time dependency on Tower, so Tower being down
still means no deploys but not red PRs. `npm ci` pins the resolved commit in
`package-lock.json`, so each app upgrades on its own schedule.

The tag is a **fixed pointer, not a range**. Nothing in RTO changes until someone
edits that string in RTO's `package.json`. Never point it at `#main`.

**Rejected: GitHub Packages.** Its npm registry requires an auth token even for
public packages. For a one-developer org that's ceremony protecting a stylesheet
from its own author.

**Rejected: Nexus.** Would force both frontend jobs onto self-hosted runners, add
Tower as a *build-time* single point of failure, need insecure-registry config
(Nexus is plain HTTP), and require standing up an npm group repo proxying npmjs or
`npm ci` couldn't resolve Angular either. Nexus earns its place for images because
images must reach Tower anyway. CSS doesn't.

**Rejected: vendored copy with a CI drift check.** Can't express "RTO is
deliberately on v0.3 while MM is on v0.4" — the check is binary, so either every app
upgrades in lockstep or you weaken it until it means nothing.

**Rejected: git submodule.** Gives a SHA rather than a version, so "which version of
the language is RTO on" has no readable answer.

## D3 — Density: 14px base on a 4px unit, with a 32:12 answer-to-evidence ratio

**Context.** Three candidates were rendered on the same screens: Instrument (13px,
everything equal weight), Ledger (14px, answer large), Calm (16px, 8px unit).

**Decision.** Ledger. Base 14px, small 12px, headline figure 32px, spacing unit 4px,
row height ~36px, radius 6px, one hairline shadow.

**Reasoning.** These are thirty-second apps. You open RTO to find out whether you
need to go in tomorrow and you're gone. Instrument density is right for *monitoring* —
staring at many numbers watching for one to move — and it makes the answer read at
the same volume as the evidence, so you have to *read* the screen to find the answer
instead of seeing it.

Calm was rejected for the opposite reason and a structural one: at 52px cells, RTO's
42-cell month calendar has to abandon Calm's density to exist at all, and **a system
its hardest screen opts out of isn't a system**. Ledger's airiness comes from
multiples of 4, not from a bigger unit, so the calendar can compress to 8px gaps and
stay on the scale. Calm's 8px unit has only one compression step before it becomes
Instrument.

**Consequences.** Both apps are already accidentally on a 4px scale — MM on
0.25rem, RTO on Tailwind's — so this ratifies something real and is the cheapest of
the three to refactor onto.

## D4 — Colour: Harbor

**Context.** Three complete palettes were rendered light and dark, with contrast
ratios and a live deuteranopia simulation.

**Decision.** Harbor — neutrals with a faint blue-green cast, a deep navy accent
(`#2a4d9b`), teal for good, burnt amber for caution, a crimson-leaning critical.
Full values in Part 3.

**Reasoning.** Colour's job here is *meaning*, not decoration. Signal used colour for
structure too, which is pleasant but means the screen is already colourful before
anything is wrong, so a real warning has less to push against. Slate failed the other
way: its muted critical read at roughly the same volume as "on track", which is a
defect in a tool whose entire job is telling you when to act.

Harbor also has the widest status separation under simulation and the strongest
accent contrast at 8.0:1 — which matters because the accent is also the focus ring.

### The finding that shaped everything else

Every candidate was run through a deuteranopia simulation (~8% of men), then a sweep
of several thousand green/amber/red combinations looked for one that stays
distinguishable while each colour keeps 4.5:1 legibility.

**None does.** The best trio anywhere in that space separates its closest pair by
**1.70:1**, and only by making critical so dark (`#58130e`) it reads as ink rather
than alarm. Two swatches need roughly 1.4:1 to read as different. Dark mode is worse —
every status colour must be light to stay legible, which compresses the differences
further, and nothing exceeds about 1.3:1.

**Therefore: the icon and the label are the encoding; colour is reinforcement.**
`compliance-status.util.ts` already does this with `○ ✓ ▲ ⚠ ✕`. That was the one part
of RTO's interface that was designed rather than defaulted, and it is now a rule the
whole language inherits.

### Correction to `UX_RECOMMENDATIONS.md` #7

That finding says the calendar's single-hue green gradient isn't colourblind-safe and
proposes a blue-to-purple gradient. **The stated reasoning is wrong.** RTO's
green-100/300/500/700 ramp measures **1.32 / 1.62 / 2.19** under deuteranopia — it
survives, because lightness carries it, and a monotonic lightness ramp is one of the
*better* devices for colourblind viewers. The proposed fix would fix nothing broken.

**The real defect is a hue collision the audit missed:** the ramp is green, and green
means "good," so a *quantity* (hours in the office) is drawn in the colour of a
*verdict*. The ramp therefore moves to the **accent** hue, freeing green to mean only
"you're fine."

### Live contrast failures in RTO today

| Utility | Uses | Ratio | |
|---|---|---|---|
| `text-gray-400` | 40 | 2.60:1 | fails 4.5:1 |
| `text-gray-300` | 15 | 1.47:1 | fails badly |
| `text-gray-500` | 69 | 4.84:1 | passes, no margin |

This is why there are exactly **three** ink levels and no dimmer fourth. The slot
`text-gray-400` occupies does not exist, deliberately.

## D5 — Character: Almanac

**Context.** Harbor's colours held constant, three typographic and structural
treatments were rendered across all three apps.

**Decision.** Almanac.

- **Interface:** Public Sans
- **Figures and headings:** Newsreader (serif), tabular lining numerals
- **Metadata:** system monospace stack — no third webfont
- **Signature:** a hairline rule beneath every label, using `--rz-rule-sig`
- **Separation:** rules, never shadows

**Reasoning.** The serif numeral does three things at once. It is immediately
not-stock — nobody puts a serif in a dashboard, and that single choice is more
distinctive than any accent hue, at no functional cost since Newsreader has proper
tabular figures. It fits what these apps are: a personal record, not telemetry.
And it is the only one of the three that survives the dinner planner, where
monospace cooking times read as a maintenance log.

Quarto was the real contender and lost on **theme durability** — see below.

### Dark mode is not neutral between structural signatures

An earlier claim in this process — that typefaces don't change with the theme, so
dark mode wouldn't affect this choice — was wrong. The typefaces don't; the
*separation devices* do.

**A drop shadow works by darkening the ground behind a surface. On a near-black
ground there is nothing left to darken.**

| Device | Light | Dark | |
|---|---|---|---|
| rule on surface | 1.30:1 | 1.27:1 | survives unchanged |
| border on surface | 3.06:1 | 3.10:1 | survives unchanged |
| drop shadow | visible | **inert** | needs a border |
| row banding | 1.11:1 | 1.11:1 | too faint alone |

Quarto's defining rule is "no rules anywhere," and dark mode forces it to take a
border. A signature that inverts itself in the theme the user actually uses isn't
that character with an asterisk; it's a different character half the time. Almanac
and Console both needed **zero** structural adaptation.

**The general rule: prefer separation devices that measure the same in both themes.**

## D6 — Where the foundation stops

**Context.** The risk is a foundation overfitted to two apps, or scope-crept into a
component library. Both are real.

**Decision.** Three tiers, sorted by *how likely you are to be wrong*:

1. **Tokens** — values with no opinion about markup. Nearly impossible to get wrong,
   so be generous.
2. **Controls** — pieces whose shape isn't in question. A button is a button in every
   app that has ever existed. Low risk.
3. **Patterns** — assemblies whose shape is app-specific. High risk, because you'd be
   guessing at structure.

**The promotion test:** *is this thing's shape dictated by the design language, or by
one app's domain?* Language → tier 2. Domain → tier 3.

**A rejected earlier version of this test, recorded because it's a tempting mistake:**
"promote when the *second* app needs it." That only works if the second app is
finished. Money Manager isn't — its missing navigation, cards and toasts are a todo
list, not a set of decisions. Reading emptiness as evidence let build order stand in
for need, and it wrongly excluded navigation, which every app requires.

**Consequences.** Navigation is tier 2, but as **parts** — `nav-item` with its
current/hover/focus/collapsed states, `nav-brand`, `nav-foot` — composable into a
sidebar, top bar or bottom bar. The destinations differ between apps; the shell
doesn't. Shipping "the RTO sidebar" would impose one app's layout on all of them.

### What the first integration found — v0.2.0

Money Manager adopted these parts, and the gap between what this section promises and
what `controls.css` shipped surfaced within an hour of someone trying to build a bottom
bar with them.

**Two of the three arrangements were unreachable.** `.rz-nav` hardcoded
`flex-direction: column` — three lines below a comment instructing the reader to arrange
it as a sidebar, a top bar or a bottom bar. Every app wanting either of the other two
would have written the same override, which is a shared language issuing an instruction
it cannot carry out. `.rz-nav--horizontal` closes it, and turns the brand's and the
foot's separating rules with the axis, because a `border-bottom` on a brand sitting in a
row draws a line under one item rather than between two.

**The one mobile arrangement broke the touch commitment.** `.rz-nav-item` took
`--rz-control-h` — 32px, a pointer height — and it was the only height available. Part 4
commits to 44px for anything a thumb hits, and in a bottom bar that is every item in it.
`rz-btn--lg` had existed for this since v0.1.0 with no navigation counterpart;
`.rz-nav--touch` is that counterpart. It is opt-in rather than a media query because the
library cannot know which of an app's arrangements is the touch one.

**And this document named a part that has never existed.** The list above read
`nav-utility`; the shipped part is `nav-foot`. Part 6 rule 3 exists to stop exactly this,
and it still happened — because that rule binds the guide to the *tokens*, which ship in
the same commit, and says nothing about the guide's prose describing `controls.css`. The
useful correction is not "be more careful": it is that **the specimen page is the only
mechanism here that fails when a claim stops being true**, so a claim not exercised by
`preview.html` is a claim nothing checks. The bottom bar is now in it.

None of this was visible before an app tried it. That is the argument for adopting a
language in the smaller codebase first, and it is worth restating for RTO: these are the
defects that survived a full design process, written down, reviewed, and gated on CI.

**Card is a deliberate exception.** MM has none today, so the promotion test says tier
3. It's tier 2 anyway, because every specimen shows MM's tables and forms in cards and
the refactor introduces them immediately. It's the only item where "does both apps
have it" and "will both use it once we're done" disagree.

**Deliberately not here:** menus, modals, sheets, toasts, calendar grid, gauge,
charts, meal cards, balance projection. Not because they're unimportant — because
nothing has yet established what shape they take. RTO's bottom sheet exists for a
mobile calendar day-detail; whether that's a language pattern or a calendar accident
is genuinely unanswerable until a second app wants one, and **the overlap between the
two is the real component**.

Resist the tempting middle move of a shared "overlay primitive" for menus, modals and
sheets to sit on. Its shape depends entirely on what ends up sitting on it.

## D7 — Space, depth, states

**Spacing:** nine steps on a 4px base — 2, 4, 8, 12, 16, 24, 32, 48, 64. Gaps widen
as values grow, because the eye notices 4→8 far more than 48→52.

6px, 10px and 20px are **dropped** despite 60 uses in RTO today. Those are nudges, and
the cases that genuinely needed 6px are better served by a different token: **control
heights are explicit** (28 / 32 / 44px) rather than derived from padding. RTO reaches
for `py-1.5` 28 times, always to land a small control on a sensible height. Specify
the height and padding just centres the content.

**Radius:** five values — 0, 4, 6, 10, full. Down from RTO's seven. Almanac separates
with rules, so heavy rounding would fight the character. `full` is for dots, avatars
and the gauge — not badges.

**Elevation:** one scale, **two mechanisms**. Light resolves to a shadow; dark
resolves to a lighter surface plus a border, because shadows are inert there. Each
dark step is only 1.11:1 from the one below — perceptible but not sufficient alone,
which is why the border is mandatory.

`e2` and `e3` have no user in either app yet. They exist because **a scale with holes
gets filled by invention**, and inventing a z-index is how RTO ended up with `z-[200]`
and `z-[300]`.

**States — the three-zone rule.** RTO currently renders *today*, *selected* and
*keyboard-focused* as the same blue ring on the one grid you navigate with arrow keys.

| State | Zone | Treatment |
|---|---|---|
| Focus | **outside** the box | 2px accent outline, 2px offset. Keyboard only, never removed. |
| Selected | **on** the box | 12% accent tint fill, accent border |
| Current | **inside** the box | 4px accent dot beneath the figure |

All three can be true simultaneously and each stays readable, because each occupies
space the others don't. This generalises to any element with overlapping states.

**Disabled is a token swap, not opacity.** Fading a control fades its border and
shadow too, and a disabled control still needs a visible boundary. The swap lands at
2.4:1 light and 3.1:1 dark — clearly inert, still readable. WCAG exempts disabled
controls from 4.5:1; "exempt" is not "illegible."

**Pressed doesn't move anything.** No transforms or nudges — they read as gimmicks on
desktop and misfire on touch. Pressed is one surface step darker than hover.

**Current-page in navigation** uses the tinted fill (`--rz-accent-tint`, the same
token as `selected`). A marker rule was the alternative and would have reused
Almanac's own device; the tinted fill was chosen for legibility at a glance. It must
stay at the 12% tint — the failure mode is creeping back toward the saturated block
RTO has today, which makes *where you already are* the loudest thing on screen.

---

# Part 3 — Token reference

All values verified: text ≥4.5:1, control borders ≥3:1, ramp monotonic in lightness
and stepped in deuteranopia simulation.

Everything is prefixed `--rz-`. **This matters:** Tailwind v4 defines `--color-blue-600`
and friends as real custom properties, so an unprefixed `--color-primary` would sit in
the framework's own namespace. That is how you get a collision nobody can find.

### Colour

| Token | Light | Dark | Checked |
|---|---|---|---|
| `--rz-ground` | `#f1f4f4` | `#0e1416` | page background |
| `--rz-surface` | `#ffffff` | `#171f22` | cards, panels |
| `--rz-surface-2` | `#ffffff` | `#1e282c` | floating (e2) |
| `--rz-surface-3` | `#ffffff` | `#253138` | overlay (e3) |
| `--rz-rule` | `#dde3e4` | `#283236` | decorative dividers |
| `--rz-rule-sig` | `#bcc8c9` | `#3b4a4f` | 1.7 / 1.8:1 — the signature hairline |
| `--rz-control` | `#87969a` | `#5d6d72` | 3.1:1 — input and button borders |
| `--rz-ink` | `#0f1a1d` | `#e4ecee` | 17.7 / 14.0:1 |
| `--rz-ink-2` | `#52646a` | `#94a5aa` | 6.2 / 6.6:1 |
| `--rz-ink-3` | `#64757b` | `#83949a` | 4.8 / 5.3:1 |
| `--rz-accent` | `#2a4d9b` | `#79a6e8` | 8.0 / 6.7:1 |
| `--rz-on-accent` | `#ffffff` | `#0e1416` | 8.0 / 7.5:1 |
| `--rz-accent-tint` | `#e5eaf3` | `#232f3a` | selected fill, nav current |
| `--rz-good` | `#0d6b62` | `#3ec2b1` | 5.3 / 6.8:1 on its tint |
| `--rz-good-bg` | `#ddeeec` | `#0f2b28` | |
| `--rz-warn` | `#a25b07` | `#e8a552` | 4.6 / 7.3:1 on its tint |
| `--rz-warn-bg` | `#fbeedd` | `#2f2211` | |
| `--rz-crit` | `#8c1330` | `#f78ba0` | 7.8 / 7.2:1 on its tint |
| `--rz-crit-bg` | `#fbe6ea` | `#33161e` | |
| `--rz-disabled-fg` | `#97a2a6` | `#626f74` | 2.4 / 3.1:1 |
| `--rz-disabled-bg` | `#f1f4f4` | `#1a2226` | |
| `--rz-disabled-border` | `#dde3e4` | `#283236` | |
| `--rz-hover` | `#f1f4f4` | `#1e282c` | |
| `--rz-pressed` | `#e6ebec` | `#253138` | |

**Sequential ramp** — a *quantity*, never a verdict. Accent-hued, monotonic in
lightness. Deuteranopia steps: 1.45 / 1.67 / 2.78 light, 1.27 / 1.42 / 2.42 dark.

| Token | Light | Dark |
|---|---|---|
| `--rz-ramp-1` | `#e5ebf5` | `#16222e` |
| `--rz-ramp-2` | `#b6c6e2` | `#1f3450` |
| `--rz-ramp-3` | `#7d99c9` | `#2b4a7d` |
| `--rz-ramp-4` | `#2a4d9b` | `#5d87c9` |

### Type

| Role | Face | Size | Weight | Notes |
|---|---|---|---|---|
| `--rz-figure-lg` | Newsreader | 32px | 500 | the answer; tabular lining |
| `--rz-figure` | Newsreader | 20px | 500 | secondary figures, totals |
| `--rz-title` | Public Sans | 15px | 600 | card and section titles |
| `--rz-body` | Public Sans | 14px | 400 | default |
| `--rz-small` | Public Sans | 12px | 400 | evidence, captions |
| `--rz-label` | Public Sans | 10px | 600 | uppercase, .11em, + hairline |
| `--rz-meta` | system mono | 10px | 400 | version, sha, timestamps |

Line heights: 1.55 body, 1.3 titles, 1 figures. `font-variant-numeric: tabular-nums`
on every column of digits — MM already does this by instinct; it is now a rule.

### Space, radius, elevation, layering

```
--rz-space-0   2px     --rz-radius-none  0        --rz-z-base       0
--rz-space-1   4px     --rz-radius-sm    4px      --rz-z-raised    10
--rz-space-2   8px     --rz-radius-md    6px      --rz-z-nav      100
--rz-space-3  12px     --rz-radius-lg   10px      --rz-z-floating 200
--rz-space-4  16px     --rz-radius-full 9999px    --rz-z-overlay  300
--rz-space-6  24px                                --rz-z-toast    400
--rz-space-8  32px     --rz-control-h-sm  28px
--rz-space-12 48px     --rz-control-h     32px
--rz-space-16 64px     --rz-control-h-lg  44px
```

| Elevation | Light | Dark |
|---|---|---|
| `e0` flush | no shadow | surface = ground |
| `e1` raised | `0 1px 2px rgba(15,26,29,.10)` | `--rz-surface` + 1px border |
| `e2` floating | `0 4px 12px rgba(15,26,29,.12)` | `--rz-surface-2` + 1px border |
| `e3` overlay | `0 12px 32px rgba(15,26,29,.18)` | `--rz-surface-3` + 1px border |

---

# Part 4 — Accessibility commitments

Mechanical and checkable. Verify these rather than trusting them.

- **Text contrast ≥ 4.5:1** against its own background, both themes. Every ink level,
  every status colour on its own tint, the accent on surface, and `on-accent` on
  accent.
- **Control boundaries ≥ 3:1.** `--rz-control` is the token for anything that bounds
  an input or a button. `--rz-rule` is decorative and deliberately below that
  threshold — do not use it for a control.
- **Visible focus on everything focusable.** 2px accent outline at 2px offset, and it
  is never the same treatment as selected or current.
- **Touch targets:** 44px for anything a thumb hits; 24×24 is the absolute floor
  (WCAG 2.5.8).
- **No meaning in hue alone.** Every status carries an icon whose *shape* differs and
  a text label. The sequential ramp is monotonic in lightness.
- **Respect `prefers-reduced-motion`.** The skeleton pulse and every transition stop.
- **Disabled stays readable** — ≥2:1, even though WCAG exempts it.

---

# Part 5 — Extending this

**Before adding anything, apply the promotion test from D6:** is its shape dictated
by the design language, or by one app's domain?

If the domain — it belongs in the app, not here. Build it there, and when a second app
needs the same thing, the *overlap between the two implementations* is the component
worth promoting. Not the first implementation.

If the language — add it, and record the decision here with its reasoning. A decision
without its reasoning gets re-litigated the first time someone disagrees with it.

**Any new colour must clear the checks in Part 4 before it ships.** `contrast.py` in
this repo runs them.

---

# Part 6 — Versioning

Semantic versioning, and it means more here than usual because **CSS has no compiler**.
Rename a class and the app builds, the tests pass, and a control silently renders
unstyled.

1. **Class names and token names are public API.** Renaming one is a **major**, the
   same as changing a method signature.
2. **Nothing is deleted in a minor.** A replaced class stays as an alias for one major
   cycle. In CSS an alias costs one line; there is no excuse.
3. **Every version's changes are recorded here, in the same commit as the code.** This
   is the whole reason the guide and the tokens ship as one artifact — a guide that can
   drift from its tokens is worse than no guide, because you'll trust it and it'll be
   wrong.

Apps pin a tag and upgrade deliberately:

```json
"@rezatron-labs/design": "github:rezatron-labs/platform-design#v0.1.0"
```

Never `#main`. A branch pointer gives two apps different bytes on different install
dates, which is the exact failure this is built to prevent.

---

# Appendix — Conclusions that were wrong

Recorded because knowing which prior reasoning failed is worth more than a clean
document.

1. **"The calendar's green ramp isn't colourblind-safe."** (`UX_RECOMMENDATIONS.md`
   #7.) It measures 1.32 / 1.62 / 2.19 under deuteranopia — it survives. The real
   defect is that it shares a hue with the "good" status, so a quantity reads as a
   verdict.
2. **"Promote a component when the second app needs it."** Only valid if the second
   app is finished. MM's emptiness was build order, not evidence. Cost: nearly
   excluded navigation, which every app requires.
3. **"Typefaces don't change with the theme, so character is theme-neutral."** True of
   the faces, false of the structural signatures. Shadows are inert on a near-black
   ground; rules and borders are not. This is what decided Almanac over Quarto.
4. **"Colour cannot separate status under deuteranopia at all."** An overcorrection
   from a first pass where all three candidates happened to share a lightness. The
   sweep proved ~1.70:1 is achievable — enough to matter in light mode, not enough in
   dark. The conclusion (icon and label carry meaning) stands; the absolute version of
   it didn't.
