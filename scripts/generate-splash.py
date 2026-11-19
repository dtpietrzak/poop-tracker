#!/usr/bin/env python3
"""Generate Apple PWA splash screens (apple-touch-startup-image) for Poop Tracker.

Renders one PNG per device size and orientation into public/splash/, and prints
the <link> tags to paste into public/index.html (between the SPLASH markers;
pass --write to replace them automatically).

Requires rsvg-convert (librsvg).

    python3 scripts/generate-splash.py --write
"""
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "splash"
INDEX = ROOT / "public" / "index.html"

# (label, CSS width, CSS height, device pixel ratio), portrait sizes.
DEVICES = [
    ("iPhone 16/17 Pro Max", 440, 956, 3),
    ("iPhone Air", 420, 912, 3),
    ("iPhone 16/17 Pro, 17", 402, 874, 3),
    ("iPhone 14/15 Pro Max, 15/16 Plus", 430, 932, 3),
    ("iPhone 14 Pro, 15, 15 Pro, 16", 393, 852, 3),
    ("iPhone 12/13 Pro Max, 14 Plus", 428, 926, 3),
    ("iPhone 12, 13, 14, 16e", 390, 844, 3),
    ("iPhone X, XS, 11 Pro, 12/13 mini", 375, 812, 3),
    ("iPhone XS Max, 11 Pro Max", 414, 896, 3),
    ("iPhone XR, 11", 414, 896, 2),
    ("iPhone 8 Plus", 414, 736, 3),
    ("iPhone 8, SE 2/3", 375, 667, 2),
    ("iPhone SE 1", 320, 568, 2),
    ("iPad Pro 13 (M4)", 1032, 1376, 2),
    ("iPad Pro 12.9", 1024, 1366, 2),
    ("iPad Pro 11 (M4)", 834, 1210, 2),
    ("iPad Pro 11, Air 11", 834, 1194, 2),
    ("iPad Air 10.9, iPad 10th gen", 820, 1180, 2),
    ("iPad Air 10.5", 834, 1112, 2),
    ("iPad 10.2", 810, 1080, 2),
    ("iPad mini 6/7", 744, 1133, 2),
    ("iPad 9.7, mini 1-5", 768, 1024, 2),
]

POOP = """
  <g fill="url(#poo)" stroke="#3b2010" stroke-width="10" stroke-linejoin="round">
    <ellipse cx="256" cy="372" rx="150" ry="58"/>
    <ellipse cx="256" cy="300" rx="116" ry="50"/>
    <ellipse cx="256" cy="236" rx="80" ry="42"/>
    <path d="M216 210 C 230 150, 270 140, 290 110 C 300 160, 296 200, 296 210 Z"/>
  </g>
  <circle cx="214" cy="300" r="22" fill="#fff7ef"/>
  <circle cx="298" cy="300" r="22" fill="#fff7ef"/>
  <circle cx="219" cy="304" r="11" fill="#3b2010"/>
  <circle cx="303" cy="304" r="11" fill="#3b2010"/>
  <path d="M206 352 Q 256 392 306 352" fill="none" stroke="#3b2010" stroke-width="10" stroke-linecap="round"/>
"""


def svg(w: int, h: int) -> str:
    """Splash art in pixel units. Sizes scale with the shorter side."""
    s = min(w, h)
    poop = s * 0.34  # poop box size
    title = s * 0.105
    tag = s * 0.04
    gap = s * 0.06
    block = poop * 0.68 + gap + title  # visible poop height + gap + title
    top = (h - block) / 2 - s * 0.03
    cx = w / 2
    # The poop art occupies roughly y 105..435 and x 100..412 of its 512 box.
    scale = poop / 512
    px = cx - 256 * scale
    py = top - 105 * scale
    ty = top + 330 * scale + gap + title * 0.78
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.6" y2="1">
      <stop offset="0" stop-color="#8a5229"/>
      <stop offset="1" stop-color="#3b2010"/>
    </linearGradient>
    <linearGradient id="poo" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#c98a52"/>
      <stop offset="1" stop-color="#8f5426"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#ffd9b0" stop-opacity="0.28"/>
      <stop offset="1" stop-color="#ffd9b0" stop-opacity="0"/>
    </radialGradient>
    <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="{s*0.012:.1f}" stdDeviation="{s*0.014:.1f}" flood-color="#1c0e05" flood-opacity="0.45"/>
    </filter>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  <circle cx="{cx:.1f}" cy="{top + poop*0.4:.1f}" r="{poop*0.9:.1f}" fill="url(#glow)"/>
  <g transform="translate({px:.1f} {py:.1f}) scale({scale:.4f})" filter="url(#shadow)">{POOP}</g>
  <text x="{cx:.1f}" y="{ty:.1f}" text-anchor="middle" font-family="Noto Sans, Liberation Sans, sans-serif"
        font-size="{title:.1f}" font-weight="800" letter-spacing="{-title*0.02:.1f}" fill="#fff7ef">Poop Tracker</text>
  <text x="{cx:.1f}" y="{h - s*0.09:.1f}" text-anchor="middle" font-family="Noto Sans, Liberation Sans, sans-serif"
        font-size="{tag:.1f}" font-weight="600" fill="#e8d3bf" opacity="0.75">Tap a day. Log a poop.</text>
</svg>"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    links = []
    with tempfile.TemporaryDirectory() as tmp:
        for label, cw, ch, dpr in DEVICES:
            for orient in ("portrait", "landscape"):
                w, h = cw * dpr, ch * dpr
                if orient == "landscape":
                    w, h = h, w
                name = f"apple-splash-{w}x{h}.png"
                src = pathlib.Path(tmp) / f"{w}x{h}.svg"
                src.write_text(svg(w, h))
                subprocess.run(["rsvg-convert", "-o", str(OUT / name), str(src)], check=True)
                media = (
                    f"(device-width: {cw}px) and (device-height: {ch}px) and "
                    f"(-webkit-device-pixel-ratio: {dpr}) and (orientation: {orient})"
                )
                links.append(f'  <link rel="apple-touch-startup-image" media="{media}" href="splash/{name}" />')
            print(f"  {label}: {cw * dpr}x{ch * dpr}", file=sys.stderr)

    block = "\n".join(links)
    if "--write" in sys.argv:
        html = INDEX.read_text()
        pattern = re.compile(r"(  <!-- SPLASH:START.*?-->\n).*?(  <!-- SPLASH:END -->)", re.S)
        if not pattern.search(html):
            sys.exit("SPLASH markers not found in public/index.html")
        INDEX.write_text(pattern.sub(lambda m: m.group(1) + block + "\n" + m.group(2), html))
        print(f"Wrote {len(links)} splash links into {INDEX.relative_to(ROOT)}", file=sys.stderr)
    else:
        print(block)


if __name__ == "__main__":
    main()
