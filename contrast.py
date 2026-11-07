#!/usr/bin/env python3
"""Runs the accessibility checks documented in GUIDE.md Part 4.

Values are parsed out of tokens.css rather than restated here. An earlier version
hardcoded the palette, which meant this script could pass while checking colours
the library no longer shipped — the silent-drift failure the guide warns about,
reproduced in the tool meant to catch it.

Exits non-zero on failure, so CI can gate on it.

The deuteranopia simulation is here because of GUIDE.md D4: no green/amber/red trio
stays distinguishable to a deuteranope while each colour keeps 4.5:1 legibility.
Colour therefore cannot be the status channel — icon and label are. What this still
enforces is that the sequential ramp, which has no icon and no label and so genuinely
relies on colour alone, stays ordered by lightness.
"""

import pathlib
import re
import sys

TOKENS = pathlib.Path(__file__).parent / "tokens.css"

# (label, foreground token, background token, minimum ratio)
CHECKS = [
    ("body text",            "ink",         "surface",     4.5),
    ("body text on ground",  "ink",         "ground",      4.5),
    ("secondary text",       "ink-2",       "surface",     4.5),
    ("secondary on ground",  "ink-2",       "ground",      4.5),
    ("tertiary text",        "ink-3",       "surface",     4.5),
    ("accent text",          "accent",      "surface",     4.5),
    ("text on accent",       "on-accent",   "accent",      4.5),
    ("text on selected",     "ink",         "accent-tint", 4.5),
    # A badge's icon (.rz-badge__icon) inherits the badge's ink, so these three
    # and "secondary text" (the neutral badge's ink-2 on surface) hold the icon
    # to 4.5:1, above the 3:1 an icon needs as a non-text mark.
    ("good on its tint",     "good",        "good-bg",     4.5),
    ("caution on its tint",  "warn",        "warn-bg",     4.5),
    ("critical on its tint", "crit",        "crit-bg",     4.5),
    # Control boundaries, WCAG 1.4.11. --rz-rule is decorative and exempt on purpose.
    ("control boundary",     "control",     "surface",     3.0),
    # The signature hairline has to read, not merely divide.
    ("signature hairline",   "rule-sig",    "surface",     1.5),
    # WCAG exempts disabled controls from 4.5:1. "Exempt" is not "illegible".
    ("disabled text",        "disabled-fg", "disabled-bg", 2.0),
    # A chart series is a non-text mark, so WCAG 1.4.11's 3:1 is its threshold.
    # Checked against the ground as well as the surface, because a chart is
    # drawn on whichever the screen puts it on.
    ("chart series 1",       "series-1",    "surface",     3.0),
    ("series 1 on ground",   "series-1",    "ground",      3.0),
    # The focus ring sits outside the element, so it is seen against whatever
    # the element stands on: a card's surface or the page's ground. A ring is a
    # non-text indicator, so 3:1 (WCAG 1.4.11). --rz-focus is an alias of the
    # accent by default; the parser resolves it per theme before this runs.
    ("focus ring",           "focus",       "surface",     3.0),
    ("focus ring on ground", "focus",       "ground",      3.0),
    # .rz-btn--danger-quiet: critical ink with no fill, so at rest it is read
    # against whatever it stands on. Its hover fill is --rz-crit-bg, the same
    # pairing as "critical on its tint", listed again under the button's name so
    # every state of it shows here. Its pressed fill is a mix, read out of
    # controls.css (DERIVED below).
    ("quiet danger",         "crit",        "surface",     4.5),
    ("quiet danger, ground", "crit",        "ground",      4.5),
    ("quiet danger, hover",  "crit",        "crit-bg",     4.5),
    ("quiet danger, pressed", "crit",       "danger-quiet-pressed", 4.5),
    # .rz-btn--danger-outlined shares the quiet button's rules, so its ink at
    # rest and on hover is checked above. What it adds is a critical border,
    # which bounds a control, so WCAG 1.4.11's 3:1 against whatever it stands
    # on. Its pressed fill is read from its own selector, which also proves the
    # shared rule still names it.
    ("outlined border",      "crit",        "surface",     3.0),
    ("outlined, ground",     "crit",        "ground",      3.0),
    ("outlined, pressed",    "crit",        "danger-outlined-pressed", 4.5),
]

CONTROLS = pathlib.Path(__file__).parent / "controls.css"

# Fills that controls.css mixes from two tokens rather than naming one. Each is
# read out of the rule that draws it, by selector, so the mix checked here is the
# mix that ships; restating the percentage would be the drift this file exists to
# prevent. Name -> the selector whose `background: color-mix(...)` defines it.
DERIVED = {
    "danger-quiet-pressed": ".rz-btn--danger-quiet:active",
    "danger-outlined-pressed": ".rz-btn--danger-outlined:active",
}

RAMP = ["ramp-1", "ramp-2", "ramp-3", "ramp-4"]
RAMP_MIN_STEP = 1.25  # adjacent steps, under deuteranopia simulation


# ── Parsing ────────────────────────────────────────────────────────────────────

def _body_after(css, index):
    """Given an index at or before a '{', return the text inside its matching '}'.

    Brace-counted rather than pattern-matched. A regex here silently ran past the
    end of the light block and captured the dark one, so both themes reported the
    same values and the script announced that everything passed.
    """
    start = css.index("{", index)
    depth = 0
    for i in range(start, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return css[start + 1:i]
    raise SystemExit("Unbalanced braces in tokens.css")


def _colours(text):
    return dict(re.findall(r"--rz-([a-z0-9-]+):\s*(#[0-9a-fA-F]{3,8})\s*;", text))


def _aliases(text):
    """Tokens defined as another token, such as `--rz-focus: var(--rz-accent)`."""
    return dict(re.findall(r"--rz-([a-z0-9-]+):\s*var\(--rz-([a-z0-9-]+)\)\s*;", text))


def _merge(colours, aliases, body):
    """Overlay one block's declarations, a later one replacing an earlier one.

    A token is either a colour or an alias, never both: a block that gives a hex
    to a token an earlier block aliased replaces the alias, and the reverse, as
    the cascade does.
    """
    new_colours, new_aliases = _colours(body), _aliases(body)
    for name in new_colours:
        aliases.pop(name, None)
    for name in new_aliases:
        colours.pop(name, None)
    colours.update(new_colours)
    aliases.update(new_aliases)


def _resolve(colours, aliases, theme):
    """Turn every alias into the colour it ends at, in this theme's palette.

    Resolved after the theme's blocks are merged, as the browser does, so an alias
    takes the value its target has in this theme. A missing or circular target
    stops the script rather than dropping the token, which would leave its checks
    reporting a missing token instead of the real fault.
    """
    resolved = dict(colours)
    for name in aliases:
        seen, target = [name], aliases[name]
        while target in aliases:
            if target in seen:
                raise SystemExit(f"{theme}: --rz-{name} is a circular alias "
                                 f"({' -> '.join(seen + [target])})")
            seen.append(target)
            target = aliases[target]
        if target not in colours:
            raise SystemExit(f"{theme}: --rz-{name} resolves to --rz-{target}, "
                             f"which tokens.css never gives a colour")
        resolved[name] = colours[target]
    return resolved


def parse_tokens(path):
    """Return {"light": {...}, "dark": {...}} of --rz-* colour values.

    Light is every bare `:root {` block — the colour block plus the
    theme-independent one, which contributes no colours but is harmless to merge.
    Dark is that, overlaid with the explicit `:root.dark` block, so tokens which
    don't change per theme still resolve. Aliases (`var(--rz-…)`) are merged the
    same way and then resolved per theme, so `--rz-focus` is checked as the colour
    it actually renders in each.

    The `@media (prefers-color-scheme: dark)` block is deliberately skipped: it
    carries the same values as `:root.dark` by construction, and checking one of
    the two is enough. If they ever disagree, that is a bug this won't catch —
    keep them edited together.
    """
    css = path.read_text()

    light, light_aliases = {}, {}
    for match in re.finditer(r"(?m)^:root\s*\{", css):
        _merge(light, light_aliases, _body_after(css, match.start()))
    if not light:
        raise SystemExit(f"Found no bare ':root' colour block in {path}")

    explicit_dark = re.search(r"(?m)^:root\.dark,", css)
    if not explicit_dark:
        raise SystemExit(f"Found no ':root.dark' block in {path}")

    dark, dark_aliases = dict(light), dict(light_aliases)
    _merge(dark, dark_aliases, _body_after(css, explicit_dark.start()))

    if dark == light:
        raise SystemExit("Light and dark parsed identically — the parser is wrong, "
                         "not the palette.")

    return {"light": _resolve(light, light_aliases, "light"),
            "dark": _resolve(dark, dark_aliases, "dark")}


def parse_mixes(path):
    """Return {name: (token a, weight of a, token b)} for each DERIVED fill.

    Only the form controls.css uses is understood:
    `background: color-mix(in oklab, var(--rz-a) N%, var(--rz-b))`. Anything else
    in that rule stops the script rather than being checked as something it isn't.
    The selector may stand alone or be one of a comma-separated list.
    """
    css = path.read_text()
    without_comments = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group()), css, flags=re.S)
    mixes = {}
    for name, selector in DERIVED.items():
        rule = next((m for m in re.finditer(r"([^{}]+)\{", without_comments)
                     if selector in (s.strip() for s in m.group(1).split(","))), None)
        if not rule:
            raise SystemExit(f"{selector} not found in {path.name}, so {name} "
                             "cannot be checked")
        mix = re.search(r"background:\s*color-mix\(\s*in oklab,\s*var\(--rz-([a-z0-9-]+)\)"
                        r"\s+(\d+(?:\.\d+)?)%,\s*var\(--rz-([a-z0-9-]+)\)\s*\)",
                        _body_after(css, rule.end() - 1))
        if not mix:
            raise SystemExit(f"{selector} in {path.name} has no background in the form "
                             "color-mix(in oklab, var(--rz-a) N%, var(--rz-b))")
        mixes[name] = (mix.group(1), float(mix.group(2)) / 100, mix.group(3))
    return mixes


# ── Colour maths ───────────────────────────────────────────────────────────────

def _to_rgb(colour):
    h = colour.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _to_linear(channel):
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _from_linear(value):
    v = max(0.0, min(1.0, value))
    return v * 12.92 if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055


def luminance(colour):
    r, g, b = _to_rgb(colour)
    return 0.2126 * _to_linear(r) + 0.7152 * _to_linear(g) + 0.0722 * _to_linear(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _to_oklab(colour):
    r, g, b = (_to_linear(v) for v in _to_rgb(colour))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def _from_oklab(lab):
    big_l, a, b = lab
    l = (big_l + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (big_l - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (big_l - 0.0894841775 * a - 1.2914855480 * b) ** 3
    linear = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
              -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
              -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, round(_from_linear(v) * 255))) for v in linear
    )


def mix_oklab(a, weight_a, b):
    """CSS color-mix(in oklab, a weight_a, b) for two opaque colours."""
    la, lb = _to_oklab(a), _to_oklab(b)
    return _from_oklab(tuple(weight_a * x + (1 - weight_a) * y for x, y in zip(la, lb)))


def deuteranopia(colour):
    """Vienot et al. simulation, applied in linear light."""
    r, g, b = (_to_linear(v) for v in _to_rgb(colour))
    long_ = 17.8824 * r + 43.5161 * g + 4.1193 * b
    short = 0.02996 * r + 0.18431 * g + 1.4670 * b
    medium = 0.494207 * long_ + 1.24827 * short  # the missing cone, reconstructed
    out = (
        0.0809444479 * long_ + -0.1305044090 * medium + 0.116721066 * short,
        -0.0102485335 * long_ + 0.0540193266 * medium + -0.113614708 * short,
        -0.000365296938 * long_ + -0.00412161469 * medium + 0.693511405 * short,
    )
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, round(_from_linear(v) * 255))) for v in out
    )


# ── Checks ─────────────────────────────────────────────────────────────────────

def check_theme(name, palette):
    failures = []
    print(f"\n===== HARBOR {name.upper()} =====")

    missing = {t for _, fg, bg, _ in CHECKS for t in (fg, bg)} | set(RAMP)
    missing -= palette.keys()
    if missing:
        failures.append(f"{name}: tokens.css is missing --rz-{', --rz-'.join(sorted(missing))}")
        print(f"  MISSING TOKENS: {sorted(missing)}")
        return failures

    for label, fg, bg, minimum in CHECKS:
        ratio = contrast(palette[fg], palette[bg])
        ok = ratio >= minimum
        if not ok:
            failures.append(f"{name}: {label} is {ratio:.2f}:1, needs {minimum}:1")
        print(f"  {label:22s} {palette[fg]} on {palette[bg]}  "
              f"{ratio:6.2f}:1  needs {minimum}  {'ok' if ok else 'FAIL'}")

    ramp = [palette[t] for t in RAMP]
    lums = [luminance(c) for c in ramp]
    monotonic = (all(lums[i] < lums[i + 1] for i in range(len(lums) - 1))
                 or all(lums[i] > lums[i + 1] for i in range(len(lums) - 1)))
    if not monotonic:
        failures.append(f"{name}: ramp is not monotonic in lightness")
    print(f"  {'ramp monotonic':22s} {monotonic}")

    for i in range(len(ramp) - 1):
        step = contrast(deuteranopia(ramp[i]), deuteranopia(ramp[i + 1]))
        ok = step >= RAMP_MIN_STEP
        if not ok:
            failures.append(f"{name}: ramp {i + 1}->{i + 2} is {step:.2f}:1 under "
                            f"deuteranopia, needs {RAMP_MIN_STEP}:1")
        print(f"  {'ramp ' + str(i + 1) + '->' + str(i + 2) + ' (deuter)':22s} "
              f"{step:6.2f}:1  needs {RAMP_MIN_STEP}  {'ok' if ok else 'FAIL'}")

    for i, colour in enumerate(ramp):
        best = max(contrast(palette["ink"], colour), contrast(palette["on-accent"], colour))
        ok = best >= 4.5
        if not ok:
            failures.append(f"{name}: no legible text on ramp {i + 1} ({best:.2f}:1)")
        print(f"  {'text on ramp ' + str(i + 1):22s} {colour}  "
              f"{best:6.2f}:1  needs 4.5  {'ok' if ok else 'FAIL'}")

    return failures


def main():
    if not TOKENS.exists():
        print(f"tokens.css not found at {TOKENS}")
        return 1

    themes = parse_tokens(TOKENS)
    print(f"Parsed {len(themes['light'])} light and {len(themes['dark'])} dark "
          f"colour tokens from {TOKENS.name}")

    mixes = parse_mixes(CONTROLS)
    for name, (a, weight_a, b) in mixes.items():
        for palette in themes.values():
            if a in palette and b in palette:
                palette[name] = mix_oklab(palette[a], weight_a, palette[b])
        print(f"Derived {name} from {CONTROLS.name}: "
              f"color-mix(in oklab, --rz-{a} {weight_a:.0%}, --rz-{b})")

    failures = check_theme("light", themes["light"]) + check_theme("dark", themes["dark"])

    print()
    if failures:
        print("FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("All checks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
