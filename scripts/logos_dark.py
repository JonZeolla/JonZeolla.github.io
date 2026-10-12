#!/usr/bin/env python3
"""Make dark-mode variants of the "Trusted by" logos.

  python3 -I scripts/logos_dark.py            # public/wm/*.svg -> public/wm-dark/*.svg

Rule: a fill or stroke that is both dark (relative luminance < 0.18) and low-saturation (< 0.45) becomes
near-white, so black wordmarks read on the dark background while saturated brand colors (Google, Walmart,
Siemens, T-Mobile) are kept. A few brand colors are dark AND saturated (Visa navy, Bank of America navy,
Capital One navy, PepsiCo navy, NASA's blue disc); those are handled by OVERRIDES. SVGs that rely on the
default black fill get a root fill. Logos that ship an official dark-background variant (ClickUp) are
listed in SKIP and copied by hand instead.

Where the originals come from: Wikimedia Commons (search "<brand> logo svg", download via
https://commons.wikimedia.org/wiki/Special:FilePath/<File name>), or the brand's own press/brand page.
Strip any <!DOCTYPE ...> declaration (the publisher and some tooling reject DTDs).
"""
import pathlib
import re
import shutil

SRC = pathlib.Path(__file__).resolve().parent.parent / "public" / "wm"
DST = SRC.parent / "wm-dark"
WHITE = "#f3f4f6"
OVERRIDES = {
    "#1434cb": WHITE,   # Visa
    "#012169": WHITE,   # Bank of America wordmark (the red/blue flag stays)
    "#013d5b": WHITE,   # Capital One wordmark (the swoosh stays)
    "#28458e": WHITE,   # PepsiCo wordmark (the globe stays)
    "#161d23": WHITE,   # EY wordmark (the yellow beam stays)
    "#221f1f": WHITE,   # Amazon wordmark (the orange smile stays)
    "#0f0b0b": WHITE,   # Deloitte wordmark (the green dot stays)
    "#0b3d91": "#1d56c9",  # NASA disc: lighter blue so the white lettering still reads
    "#737373": "#d0d4da",  # Microsoft wordmark gray
}
SKIP = {"clickup.svg"}  # official dark variant is committed directly


def rgb(h):
    h = h.lstrip("#")
    h = "".join(c * 2 for c in h) if len(h) == 3 else h
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(c):
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def saturation(c):
    mx, mn = max(c), min(c)
    return 0 if mx == 0 else (mx - mn) / mx


def swap(color):
    k = color.lower()
    if k == "black":
        k = "#000000"
    if k in OVERRIDES:
        return OVERRIDES[k]
    if not re.fullmatch(r"#[0-9a-f]{3}|#[0-9a-f]{6}", k):
        return color
    c = rgb(k)
    return WHITE if (luminance(c) < 0.18 and saturation(c) < 0.45) else color


def convert(svg):
    changed = set()

    def rep(m):
        original = m.group(3)
        new = swap(original)
        if new != original:
            changed.add(original)
        return f"{m.group(1)}{m.group(2)}{new}"

    out = re.sub(r"\b(fill|stroke)(=\"|:\s*)(#[0-9a-fA-F]{3,6}|black)", rep, svg)
    root = re.search(r"<svg\b[^>]*>", out).group(0)
    if " fill=" not in root:
        out = out.replace(root, root[:-1] + f' fill="{WHITE}">', 1)
        changed.add("root")
    return out, changed


def main():
    DST.mkdir(exist_ok=True)
    for p in sorted(SRC.glob("*.svg")):
        if p.name in SKIP:
            if not (DST / p.name).exists():
                shutil.copy(p, DST / p.name)
                print(f"{p.name:22s} copied (no official dark variant found; add one by hand)")
            else:
                print(f"{p.name:22s} kept official dark variant")
            continue
        out, changed = convert(p.read_text(errors="ignore"))
        (DST / p.name).write_text(out)
        print(f"{p.name:22s} {sorted(changed)}")


if __name__ == "__main__":
    main()
