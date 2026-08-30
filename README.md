# platform-design

The shared design language for Rezatron's user interfaces — the tokens, the common
controls, and the reasoning behind both.

Consumed by `rto-tracker` and `money-manager`, and by whatever comes next.

> **[GUIDE.md](GUIDE.md) is the source of truth.** Where a rendered preview, a
> screenshot or a memory disagrees with it, the guide wins. It ships in the same
> commit as `tokens.css`, so the documented values and the shipped values cannot
> drift apart without someone doing it deliberately.

## Using it

```bash
npm i "github:rezatron-labs/platform-design#v0.1.0"
```

Then, once, in the app's global stylesheet:

```css
@import "@rezatron-labs/design/tokens.css";
@import "@rezatron-labs/design/controls.css";
```

**Pin a tag, never a branch.** `#main` gives two apps different bytes on different
install dates, which is the exact failure this repo exists to prevent. Nothing in a
consuming app changes until someone edits that version string in its `package.json`.

### Why a git dependency and not a registry

Both consuming apps' frontend CI jobs run on `ubuntu-latest`, which has no route to
`nexus.home:8082`. A git dependency on a public repo needs no `.npmrc`, no token, and
no CI changes, and adds no build-time dependency on Tower. GitHub Packages was
rejected because its npm registry requires auth even for public packages. The full
comparison is in [GUIDE.md § D2](GUIDE.md).

### Local development

While the language is churning, point an app at your checkout instead of cutting a tag
for every change:

```bash
npm link ../platform-design
```

Cut tags when something stabilises, not on every edit.

## Layout

| Path | |
|---|---|
| `GUIDE.md` | The decisions and the reasoning that produced them. Read this first. |
| `tokens.css` | Values only — colour, type, space, radius, elevation, layering. |
| `controls.css` | The common controls. Framework-free plain CSS, `rz-` prefixed. |
| `tailwind-bridge.css` | Optional. Maps Tailwind v4's `@theme` onto the tokens. RTO only. |
| `preview.html` | Specimen page. Imports the real CSS, so it fails when the library does. |
| `contrast.py` | Runs the accessibility checks from GUIDE.md § 4. Exits non-zero on failure. |

Open `preview.html` directly in a browser (`file://` is fine) — it links the
stylesheets relatively, so it needs a real page context rather than an inlined
snapshot.

### If the app keeps Tailwind

RTO does, for layout. Import order matters — the bridge reads the tokens, so they
have to exist first:

```css
@import "tailwindcss";
@import "@rezatron-labs/design/tokens.css";
@import "@rezatron-labs/design/tailwind-bridge.css";
@import "@rezatron-labs/design/controls.css";
```

After that, `bg-surface` and `var(--rz-surface)` are the same value by construction.
A raw `bg-blue-600` in a template is a bug, not a style choice.

## Scope

This repo holds the **foundation**: tokens, states, and controls whose shape is
dictated by the design language rather than by one app's domain.

It deliberately does **not** hold menus, modals, sheets, toasts, calendar grids,
gauges, charts, or anything else whose shape only one app has established. The
promotion test and the reasoning are in [GUIDE.md § D6](GUIDE.md) — apply it before
adding anything.

## Changing it

Every change goes through a feature branch and a PR, like everything else in the org.

CSS has no compiler: rename a class and the app builds, the tests pass, and a control
silently renders unstyled. So **class names and token names are public API** — renaming
one is a major version, nothing is deleted in a minor, and every change is recorded in
GUIDE.md in the same commit as the code. See [GUIDE.md § 6](GUIDE.md).

Any new colour must clear the checks in GUIDE.md § 4 before it ships. `contrast.py`
runs them.
