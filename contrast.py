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
    ("good on its tint",     "good",        "good-bg",     4.5),
    ("caution on its tint",  "warn",        "warn-bg",     4.5),
    ("critical on its tint", "crit",        "crit-bg",     4.5),
    # Control boundaries, WCAG 1.4.11. --rz-rule is decorative and exempt on purpose.
    ("control boundary",     "control",     "surface",     3.0),
    # The signature hairline has to read, not merely divide.
    ("signature hairline",   "rule-sig",    "surface",     1.5),
    # WCAG exempts disabled controls from 4.5:1. "Exempt" is not "illegible".
    ("disabled text",        "disabled-fg", "disabled-bg", 2.0),
]

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


def parse_tokens(path):
    """Return {"light": {...}, "dark": {...}} of --rz-* colour values.

    Light is every bare `:root {` block — the colour block plus the
    theme-independent one, which contributes no colours but is harmless to merge.
    Dark is that, overlaid with the explicit `:root.dark` block, so tokens which
    don't change per theme still resolve.

    The `@media (prefers-color-scheme: dark)` block is deliberately skipped: it
    carries the same values as `:root.dark` by construction, and checking one of
    the two is enough. If they ever disagree, that is a bug this won't catch —
    keep them edited together.
    """
    css = path.read_text()

    light = {}
    for match in re.finditer(r"(?m)^:root\s*\{", css):
        light.update(_colours(_body_after(css, match.start())))
    if not light:
        raise SystemExit(f"Found no bare ':root' colour block in {path}")

    explicit_dark = re.search(r"(?m)^:root\.dark,", css)
    if not explicit_dark:
        raise SystemExit(f"Found no ':root.dark' block in {path}")

    dark = dict(light)
    dark.update(_colours(_body_after(css, explicit_dark.start())))

    if dark == light:
        raise SystemExit("Light and dark parsed identically — the parser is wrong, "
                         "not the palette.")

    return {"light": light, "dark": dark}


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
