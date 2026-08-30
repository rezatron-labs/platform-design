#!/usr/bin/env python3
"""Runs the accessibility checks documented in GUIDE.md Part 4.

Exits non-zero if any check fails, so CI can gate on it.

The deuteranopia simulation matters because of a finding in GUIDE.md D4: no
green/amber/red trio stays distinguishable to a deuteranope while each colour keeps
4.5:1 legibility. Colour therefore cannot be the status channel — icon and label are.
What this script still enforces is that the sequential ramp, which has no icon and no
label and so genuinely relies on colour alone, stays ordered by lightness.
"""

import sys

# ── Harbor. Keep in step with tokens.css and GUIDE.md Part 3. ──
LIGHT = {
    "ground": "#f1f4f4", "surface": "#ffffff", "surface-2": "#ffffff", "surface-3": "#ffffff",
    "rule": "#dde3e4", "rule-sig": "#bcc8c9", "control": "#87969a",
    "ink": "#0f1a1d", "ink-2": "#52646a", "ink-3": "#64757b",
    "accent": "#2a4d9b", "on-accent": "#ffffff", "accent-tint": "#e5eaf3",
    "good": "#0d6b62", "good-bg": "#ddeeec",
    "warn": "#a25b07", "warn-bg": "#fbeedd",
    "crit": "#8c1330", "crit-bg": "#fbe6ea",
    "disabled-fg": "#97a2a6", "disabled-bg": "#f1f4f4",
    "ramp": ["#e5ebf5", "#b6c6e2", "#7d99c9", "#2a4d9b"],
}
DARK = {
    "ground": "#0e1416", "surface": "#171f22", "surface-2": "#1e282c", "surface-3": "#253138",
    "rule": "#283236", "rule-sig": "#3b4a4f", "control": "#5d6d72",
    "ink": "#e4ecee", "ink-2": "#94a5aa", "ink-3": "#83949a",
    "accent": "#79a6e8", "on-accent": "#0e1416", "accent-tint": "#232f3a",
    "good": "#3ec2b1", "good-bg": "#0f2b28",
    "warn": "#e8a552", "warn-bg": "#2f2211",
    "crit": "#f78ba0", "crit-bg": "#33161e",
    "disabled-fg": "#626f74", "disabled-bg": "#1a2226",
    "ramp": ["#16222e", "#1f3450", "#2b4a7d", "#5d87c9"],
}

# (label, foreground, background, minimum ratio)
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

RAMP_MIN_STEP = 1.25  # adjacent ramp steps, under deuteranopia simulation


def _to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _to_linear(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _from_linear(c):
    c = max(0.0, min(1.0, c))
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def luminance(hex_colour):
    r, g, b = _to_rgb(hex_colour)
    return 0.2126 * _to_linear(r) + 0.7152 * _to_linear(g) + 0.0722 * _to_linear(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def deuteranopia(hex_colour):
    """Vienot et al. simulation, applied in linear light."""
    r, g, b = (_to_linear(v) for v in _to_rgb(hex_colour))
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


def check(theme_name, palette):
    failures = []
    print(f"\n===== HARBOR {theme_name.upper()} =====")

    for label, fg, bg, minimum in CHECKS:
        ratio = contrast(palette[fg], palette[bg])
        ok = ratio >= minimum
        if not ok:
            failures.append(f"{theme_name}: {label} is {ratio:.2f}:1, needs {minimum}:1")
        print(f"  {label:22s} {palette[fg]} on {palette[bg]}  "
              f"{ratio:6.2f}:1  needs {minimum}  {'ok' if ok else 'FAIL'}")

    ramp = palette["ramp"]
    lums = [luminance(c) for c in ramp]
    ascending = all(lums[i] < lums[i + 1] for i in range(len(lums) - 1))
    descending = all(lums[i] > lums[i + 1] for i in range(len(lums) - 1))
    if not (ascending or descending):
        failures.append(f"{theme_name}: ramp is not monotonic in lightness")
    print(f"  {'ramp monotonic':22s} {ascending or descending}")

    for i in range(len(ramp) - 1):
        step = contrast(deuteranopia(ramp[i]), deuteranopia(ramp[i + 1]))
        ok = step >= RAMP_MIN_STEP
        if not ok:
            failures.append(
                f"{theme_name}: ramp {i + 1}->{i + 2} is {step:.2f}:1 under "
                f"deuteranopia, needs {RAMP_MIN_STEP}:1"
            )
        print(f"  {'ramp ' + str(i + 1) + '->' + str(i + 2) + ' (deuter)':22s} "
              f"{step:6.2f}:1  needs {RAMP_MIN_STEP}  {'ok' if ok else 'FAIL'}")

    for i, colour in enumerate(ramp):
        best = max(contrast(palette["ink"], colour), contrast(palette["on-accent"], colour))
        ok = best >= 4.5
        if not ok:
            failures.append(f"{theme_name}: no legible text on ramp {i + 1} ({best:.2f}:1)")
        print(f"  {'text on ramp ' + str(i + 1):22s} {colour}  "
              f"{best:6.2f}:1  needs 4.5  {'ok' if ok else 'FAIL'}")

    return failures


def main():
    failures = check("light", LIGHT) + check("dark", DARK)
    print()
    if failures:
        print("FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("All checks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
