# Replica build: pulls the SSR HTML of the source page and produces a
# self-contained index.html that renders identically without depending on
# the SvelteKit runtime OR the source origin (assets are mirrored locally
# under ./assets/).
#
# Run:  python build.py
#
# Inputs:  page-source.html      (curl of the live page; refresh manually)
# Output:  index.html, assets/...

import re
import urllib.request
from pathlib import Path

LIVE_BASE = "https://e5a5-174-95-223-166.ngrok-free.app"

SOURCE = Path("page-source.html")
OUT = Path("index.html")
ASSETS = Path("assets")

# Paths the source serves that we want mirrored locally. Image/icon assets only;
# SPA route links like /, /catalog, /new?... stay pointing at LIVE_BASE because
# they're navigation, not assets, and there's no static file to mirror.
ASSET_PATHS = [
    "/logo-endpoints.svg",
    "/landing/logos/gorgias.svg",
    "/landing/logos/grammarly.png",
    "/landing/logos/shopify.svg",
    "/favicons/apple-touch-icon.png",
    "/favicons/favicon-16x16.png",
    "/favicons/favicon-32x32.png",
    "/favicons/favicon.ico",
    "/favicons/safari-pinned-tab.svg",
    "/favicons/site.webmanifest",
]


def mirror_assets() -> None:
    """Download each ASSET_PATHS entry to ./assets/<same-path>."""
    for path in ASSET_PATHS:
        out = ASSETS / path.lstrip("/")
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() and out.stat().st_size > 0:
            continue
        url = LIVE_BASE + path
        req = urllib.request.Request(url, headers={"ngrok-skip-browser-warning": "1"})
        with urllib.request.urlopen(req) as r:
            out.write_bytes(r.read())
        print(f"  fetched {path} -> {out} ({out.stat().st_size} bytes)")


def absolutize_attr(html: str) -> str:
    """Rewrite src="/..." and href="/..." to absolute against LIVE_BASE."""
    pattern = re.compile(r'\b(src|href|action)=(["\'])(/[^"\']*)\2')

    def repl(m: re.Match) -> str:
        attr, quote, val = m.group(1), m.group(2), m.group(3)
        if val.startswith("//"):
            return m.group(0)
        return f'{attr}={quote}{LIVE_BASE}{val}{quote}'

    return pattern.sub(repl, html)


def absolutize_srcset(html: str) -> str:
    """Rewrite srcset="/foo 1x, /bar 2x" — each candidate is `URL descriptor`."""
    pattern = re.compile(r'\bsrcset=(["\'])([^"\']+)\1')

    def repl(m: re.Match) -> str:
        quote, raw = m.group(1), m.group(2)
        parts = []
        for cand in raw.split(","):
            cand = cand.strip()
            if not cand:
                continue
            bits = cand.split(None, 1)
            url = bits[0]
            desc = (" " + bits[1]) if len(bits) > 1 else ""
            if url.startswith("/") and not url.startswith("//"):
                url = LIVE_BASE + url
            parts.append(url + desc)
        return f'srcset={quote}{", ".join(parts)}{quote}'

    return pattern.sub(repl, html)


def absolutize_css_urls(html: str) -> str:
    """Rewrite url(/...) inside inline <style> blocks and style="" attrs."""
    pattern = re.compile(r"url\(\s*(['\"]?)(/[^'\")\s]+)\1\s*\)")

    def repl(m: re.Match) -> str:
        quote, val = m.group(1), m.group(2)
        if val.startswith("//"):
            return m.group(0)
        return f"url({quote}{LIVE_BASE}{val}{quote})"

    return pattern.sub(repl, html)


def strip_sveltekit_runtime(html: str) -> str:
    """Remove the SvelteKit hydration <script> (keep <script type="application/ld+json">)."""
    # Match script blocks without type="application/ld+json".
    pattern = re.compile(
        r'<script\b(?![^>]*type=["\']application/ld\+json["\'])[^>]*>.*?</script>',
        re.DOTALL,
    )
    return pattern.sub("", html)


def strip_sveltekit_markers(html: str) -> str:
    """Remove the noisy <!--[-->, <!--]-->, <!--[!-->, <!----> and hex-id markers."""
    html = re.sub(r"<!--\[!?-->", "", html)
    html = re.sub(r"<!--\]-->", "", html)
    html = re.sub(r"<!---->", "", html)
    html = re.sub(r"<!--[a-z0-9]{4,12}-->", "", html)
    return html


# Center for all rings (matches HF Pro hub-orbit center). The inner and outer
# orbit ring radii (364, 572) are encoded inside DECOR_RINGS below.


# Five engine logos go around the center. Inner ring gets 2, outer ring 3.
# (cx, cy, ring, logo_filename) — positions copied verbatim from HF Pro hub-orbit.
ORBIT_SLOTS = [
    (324.106, 428.847,  "inner", "assets/logos/engine-1.svg"),
    (918.6,   801.842,  "inner", "assets/logos/engine-2.svg"),
    (667.064, 83.197,   "outer", "assets/logos/engine-3.svg"),
    (1108.0,  397.418,  "outer", "assets/logos/engine-4.svg"),
    (83.197,  886.821,  "outer", "assets/logos/engine-5.svg"),
]

# Faint outline used on slot circles AND the center circle. Matches the
# decorative ring stroke weight so containers blend with the orbit linework.
SLOT_STROKE = "rgba(0,0,0,0.10)"

# All decorative rings around the center, ordered from innermost to outermost.
# Each entry: (radius, fill_opacity, stroke_opacity). Outline strokes are
# unchanged; fills use white at decreasing opacity outward, starting at 50%
# on the innermost ring. Gaps grow monotonically (220 → 240 → 263 → 287 → 313).
DECOR_RINGS = [
    (364.0, 0.50, 0.085),   # inner orbit ring
    (571.7, 0.38, 0.075),   # outer orbit ring
    (792.0, 0.27, 0.060),
    (1032.0, 0.19, 0.045),
    (1295.0, 0.13, 0.032),
    (1582.0, 0.07, 0.022),
    (1895.0, 0.04, 0.014),
]


def build_orbit_svg() -> str:
    """Animated orbit SVG: Inference Endpoints logo centered, engine logos in
    circular slots on two concentric rotating rings (counter-spin so logos stay
    upright). Static ripple rings emanate beyond the outer ring toward the panel
    edge, with widening gaps and fading opacity."""
    slot_r = 88            # satellite circle radius
    logo_size = 116        # square area inside the slot to fit the logo

    def slot(cx: float, cy: float, ring: str, href: str) -> str:
        ix = cx - logo_size / 2
        iy = cy - logo_size / 2
        return (
            f'<g class="hub-orbit-{ring}-item" style="transform-origin: {cx}px {cy}px">'
            f'<circle cx="{cx}" cy="{cy}" r="{slot_r}" fill="white" '
            f'stroke="{SLOT_STROKE}" stroke-width="2"/>'
            f'<image href="{href}" x="{ix}" y="{iy}" width="{logo_size}" height="{logo_size}" '
            f'preserveAspectRatio="xMidYMid meet"/>'
            f'</g>'
        )

    inner_items = "".join(slot(*s) for s in ORBIT_SLOTS if s[2] == "inner")
    outer_items = "".join(slot(*s) for s in ORBIT_SLOTS if s[2] == "outer")

    # Draw rings from outermost to innermost so each successive (smaller, denser)
    # disc paints over the previous one — this gives a smooth radial fade where
    # the area near the center looks more solidly white and the outer panels
    # bleed into the page's bg-gray-50.
    rings = "".join(
        f'<circle cx="600.849" cy="649.706" r="{r}" fill="white" fill-opacity="{fop}" '
        f'stroke="#000" stroke-opacity="{sop}" stroke-width="2"/>'
        for r, fop, sop in reversed(DECOR_RINGS)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" class="hub-orbit absolute inset-0 m-auto aspect-square" viewBox="0 0 1192 1293" fill="none" overflow="visible" role="img" aria-label="Inference Endpoints supports popular inference engines" style="max-width:100%;max-height:100%">
<style>
  .hub-orbit-inner, .hub-orbit-outer {{ transform-origin: 600.849px 649.706px; animation: hub-orbit-spin 120s linear infinite; }}
  .hub-orbit-outer {{ animation-direction: reverse; }}
  .hub-orbit-inner-item {{ animation: hub-orbit-spin 120s linear infinite reverse; }}
  .hub-orbit-outer-item {{ animation: hub-orbit-spin 120s linear infinite; }}
  @keyframes hub-orbit-spin {{ to {{ transform: rotate(360deg); }} }}
  @media (prefers-reduced-motion: reduce) {{
    .hub-orbit-inner, .hub-orbit-outer, .hub-orbit-inner-item, .hub-orbit-outer-item {{ animation: none; }}
  }}
</style>
{rings}
<circle cx="600.849" cy="649.706" r="142.583" fill="white" stroke="{SLOT_STROKE}" stroke-width="2"/>
<image href="assets/logos/inference-endpoints.svg" x="510" y="559" width="182" height="182" preserveAspectRatio="xMidYMid meet"/>
<g class="hub-orbit-inner">{inner_items}</g>
<g class="hub-orbit-outer">{outer_items}</g>
</svg>'''


def inject_engine_orbit(html: str) -> str:
    """Insert the orbit SVG into the engines section's right column WITHOUT
    altering the wrapper's classes (so the panel keeps its original size).
    The SVG positions itself absolutely inside the wrapper to avoid resizing it."""
    target = '<div class="relative z-1 grid bg-gray-50 lg:col-span-3"></div>'
    if target not in html:
        return html
    orbit = build_orbit_svg()
    replacement = (
        '<div class="relative z-1 grid bg-gray-50 lg:col-span-3 overflow-hidden">'
        f'{orbit}</div>'
    )
    return html.replace(target, replacement, 1)


# ---------- Cube-pattern style (alternate to the orbit graphic) ----------

CUBE_PATTERN_COLOR = "#EDEFF2"


def build_cube_pattern_svg(
    R: float = 30.0,
    line_width: float = 1.0,
    dot_radius: float = 1.8,
) -> str:
    """Repeating SVG pattern of isometric 3D cubes — pointy-top hexagonal cells
    with three internal lines from center to alternating vertices (the visible
    cube edges) and a dot at every vertex.

    The pattern cell holds 2 hexagons offset so the tiling forms a continuous
    honeycomb without seams. Pure decoration, aria-hidden."""
    from math import sqrt
    s3 = sqrt(3)
    pw = R * s3           # pattern cell width
    ph = R * 3            # pattern cell height
    color = CUBE_PATTERN_COLOR

    # Two hex centers that produce a seamless honeycomb when the cell tiles:
    # one fully inside the cell, one straddling the left/right edges.
    centers = [(R * s3 / 2, R), (0.0, 5 * R / 2)]

    def hex_verts(cx: float, cy: float):
        # Pointy-top hexagon vertices: top, top-right, bottom-right, bottom, bottom-left, top-left.
        return [
            (cx,             cy - R),
            (cx + R * s3 / 2, cy - R / 2),
            (cx + R * s3 / 2, cy + R / 2),
            (cx,             cy + R),
            (cx - R * s3 / 2, cy + R / 2),
            (cx - R * s3 / 2, cy - R / 2),
        ]

    path_cmds: list[str] = []
    dot_circles: list[str] = []
    for cx, cy in centers:
        v = hex_verts(cx, cy)
        # Outer hexagon outline.
        path_cmds.append(
            "M {:.3f} {:.3f} L {:.3f} {:.3f} L {:.3f} {:.3f} "
            "L {:.3f} {:.3f} L {:.3f} {:.3f} L {:.3f} {:.3f} Z".format(*[c for p in v for c in p])
        )
        # Three internal lines from center to top / bottom-left / bottom-right
        # — these are the visible "back edges" of the cube corner.
        for idx in (0, 2, 4):
            path_cmds.append(
                f"M {cx:.3f} {cy:.3f} L {v[idx][0]:.3f} {v[idx][1]:.3f}"
            )
        # Dots at every vertex + the center (where three lines meet).
        for px, py in v + [(cx, cy)]:
            dot_circles.append(
                f'<circle cx="{px:.3f}" cy="{py:.3f}" r="{dot_radius}" fill="{color}"/>'
            )

    path_d = " ".join(path_cmds)
    dots = "".join(dot_circles)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" class="absolute inset-0 w-full h-full" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <pattern id="cube-grid" patternUnits="userSpaceOnUse" width="{pw:.3f}" height="{ph:.3f}">
      <path d="{path_d}" stroke="{color}" stroke-width="{line_width}" fill="none"/>
      {dots}
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#cube-grid)"/>
</svg>'''


def inject_engine_cube_pattern(html: str) -> str:
    """Fill the engines section's right column with the isometric cube
    pattern (alternative to the orbit graphic)."""
    target = '<div class="relative z-1 grid bg-gray-50 lg:col-span-3"></div>'
    if target not in html:
        return html
    pattern_svg = build_cube_pattern_svg()
    replacement = (
        '<div class="relative z-1 grid bg-gray-50 lg:col-span-3 overflow-hidden">'
        f'{pattern_svg}</div>'
    )
    return html.replace(target, replacement, 1)


def localize_assets(html: str) -> str:
    """Rewrite each mirrored asset URL (LIVE_BASE/path) to a local relative
    path ./assets/path. Anything not in ASSET_PATHS is left alone."""
    for path in ASSET_PATHS:
        absolute = LIVE_BASE + path
        local = "assets" + path  # e.g. "assets/favicons/favicon.ico"
        html = html.replace(absolute, local)
    return html


def main() -> None:
    html = SOURCE.read_text(encoding="utf-8")

    mirror_assets()

    html = strip_sveltekit_runtime(html)
    html = strip_sveltekit_markers(html)
    html = absolutize_attr(html)
    html = absolutize_srcset(html)
    html = absolutize_css_urls(html)
    html = localize_assets(html)
    html = inject_engine_cube_pattern(html)

    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} ({len(html):,} chars)")


if __name__ == "__main__":
    main()
