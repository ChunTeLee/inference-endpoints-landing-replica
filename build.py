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


LOGO_TEXT_COLOR = "#1F2937"   # dark slate for engine labels
LOGO_ANIM_COLOR = "#FF2A4A"   # IE brand red — used for animated shooting dots
LOGO_TILE_R = 54.0            # hex radius used for the engines panel
VIEWBOX_W = 800.0
VIEWBOX_H = 440.0


def _engine_to_ie_paths(R: float) -> list[list[tuple[float, float]]]:
    """Waypoint sequences for the engine→IE shooting-line animation.

    11 paths total — each engine has 2 source dots, except Transformers
    which has 3 (one from each of its 3 top vertices). Every path
    traverses existing cube-grid edges / internal Y-arms and terminates
    at a vertex of the IE tile (a connection point of the central
    chevron hex)."""
    from math import sqrt
    s3 = sqrt(3)
    return [
        # ---- SGL (upper-left): 2 sources from its bottom edge ----
        # A: bottom-right vertex → gap-tile center → IE top
        [(-R*s3/2, -5*R/2), (-R*s3/2, -3*R/2), (0, -R)],
        # B: bottom vertex → south vertical edge → IE top-left
        [(-R*s3,   -2*R),    (-R*s3, -R),       (-R*s3/2, -R/2)],
        # ---- vLLM (upper-right): mirror of SGL ----
        [(R*s3/2,  -5*R/2),  (R*s3/2, -3*R/2),  (0, -R)],
        [(R*s3,    -2*R),    (R*s3, -R),        (R*s3/2, -R/2)],
        # ---- LLaMA (left): 2 sources from its right edge ----
        # Top arm: top-right → over apex → IE top-left
        [(-3*R*s3/2, -R/2),  (-R*s3, -R),       (-R*s3/2, -R/2)],
        # Bot arm: bottom-right → through gap-tile center → IE bottom-left
        [(-3*R*s3/2, R/2),   (-R*s3, 0),        (-R*s3/2, R/2)],
        # ---- TGI (right): mirror of LLaMA ----
        [(3*R*s3/2,  -R/2),  (R*s3, -R),        (R*s3/2, -R/2)],
        [(3*R*s3/2,  R/2),   (R*s3, 0),         (R*s3/2, R/2)],
        # ---- Transformers (below): 3 sources from its top three vertices ----
        # Left: top of left tile → above-tile center → IE bottom-left
        [(-R*s3, 2*R),       (-R*s3/2, 3*R/2),  (-R*s3/2, R/2)],
        # Middle: top of middle tile → IE bottom (single straight edge)
        [(0, 2*R),           (0, R)],
        # Right: mirror of left
        [(R*s3, 2*R),        (R*s3/2, 3*R/2),   (R*s3/2, R/2)],
    ]


def _build_engine_animations(
    R: float,
    cycle_dur: float = 6.0,
    speed: float = 40.0,
    dot_radius: float = 2.0,
    color: str = LOGO_ANIM_COLOR,
    trail_length: float = 26.0,
    line_thickness: float = 1.6,
    flash_half: float = 0.022,
) -> tuple[str, str]:
    """Build the engine→IE traveling-line animations.

    Returns (defs_svg, body_svg). `defs_svg` defines a horizontal trail
    sprite (a tapered line via linear gradient) plus the gradient itself.
    `body_svg` instantiates the sprite per path with <animateMotion>, plus
    a brief pink pulse overlay on every waypoint connection point.

    11 traveling lines total, evenly staggered across the cycle so that
    at most ~5 are simultaneously visible. Speed is intentionally low
    (40 user units/sec) for a subtle feel."""
    from math import sqrt

    paths = _engine_to_ie_paths(R)
    n_paths = len(paths)
    stagger = cycle_dur / n_paths

    # --- defs: gradient + trail sprite ---
    defs = "".join([
        f'<linearGradient id="engine-line-grad" x1="0" y1="0" x2="1" y2="0">',
        f'<stop offset="0" stop-color="{color}" stop-opacity="0"/>',
        f'<stop offset="1" stop-color="{color}" stop-opacity="1"/>',
        f'</linearGradient>',
        # Trail extends from x=-trail_length (transparent tail) to x=0 (solid head).
        # Centered vertically. rx rounds the cap; the gradient hides it on the tail.
        f'<g id="engine-trail">'
        f'<rect x="{-trail_length:.2f}" y="{-line_thickness/2:.2f}" '
        f'width="{trail_length:.2f}" height="{line_thickness:.2f}" '
        f'fill="url(#engine-line-grad)" rx="{line_thickness/2:.2f}"/>'
        f'</g>',
    ])

    # --- body: one <use> per path + per-waypoint flash overlays ---
    body_parts: list[str] = []
    for idx, waypoints in enumerate(paths):
        begin = idx * stagger
        seg_lengths = [
            sqrt((waypoints[i+1][0] - waypoints[i][0])**2 +
                 (waypoints[i+1][1] - waypoints[i][1])**2)
            for i in range(len(waypoints) - 1)
        ]
        total_length = sum(seg_lengths)
        travel_time = total_length / speed
        travel_fraction = travel_time / cycle_dur

        path_d = "M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in waypoints)

        # animateMotion: travel from start (keyPoint 0) to end (keyPoint 1)
        # during the first travel_fraction of the cycle; hold at the end
        # for the remainder.
        anim_motion = (
            f'<animateMotion dur="{cycle_dur}s" begin="{begin:.3f}s" '
            f'repeatCount="indefinite" rotate="auto" path="{path_d}" '
            f'keyTimes="0; {travel_fraction:.4f}; 1" keyPoints="0; 1; 1"/>'
        )

        # Opacity envelope: invisible before travel, fade in, hold, fade out
        fade = 0.03
        op_kt = [0.0, fade, max(fade, travel_fraction - fade), travel_fraction, 1.0]
        op_vals = [0, 1, 1, 0, 0]
        op_kt_str = "; ".join(f"{t:.4f}" for t in op_kt)
        op_val_str = "; ".join(str(v) for v in op_vals)
        anim_opacity = (
            f'<animate attributeName="opacity" values="{op_val_str}" '
            f'keyTimes="{op_kt_str}" dur="{cycle_dur}s" '
            f'begin="{begin:.3f}s" repeatCount="indefinite"/>'
        )

        body_parts.append(
            f'<use href="#engine-trail" opacity="0">{anim_motion}{anim_opacity}</use>'
        )

        # Pink-pulse overlay on each waypoint connection point.
        waypoint_times = [0.0]
        cum = 0.0
        for L in seg_lengths:
            cum += L
            waypoint_times.append(cum / total_length * travel_fraction)

        for (vx, vy), t in zip(waypoints, waypoint_times):
            if t == 0.0:
                kt = [0.0, flash_half, 1.0]
                vals = [1, 0, 0]
            elif t + flash_half >= 1.0:
                kt = [0.0, t - flash_half, 1.0]
                vals = [0, 0, 1]
            else:
                kt = [0.0, t - flash_half, t, t + flash_half, 1.0]
                vals = [0, 0, 1, 0, 0]
            kt_str = "; ".join(f"{x:.4f}" for x in kt)
            vs = "; ".join(str(v) for v in vals)
            body_parts.append(
                f'<circle cx="{vx:.3f}" cy="{vy:.3f}" r="{dot_radius}" '
                f'fill="{color}" opacity="0">'
                f'<animate attributeName="opacity" values="{vs}" '
                f'keyTimes="{kt_str}" dur="{cycle_dur}s" '
                f'begin="{begin:.3f}s" repeatCount="indefinite"/>'
                f'</circle>'
            )

    return defs, "".join(body_parts)

# Each entry: (label, icon_filename, label_text_or_None, tile_coords, icon_size).
# Tile coords are (i, j): user_x = i * R*sqrt(3), user_y = j * 1.5 * R for
# even j (odd j adds half a column offset, but our layout uses even j only).
# tile_coords[0] is the icon's tile; remaining entries are text-area tiles.
# icon_size is in user units; the engines panel hex inscribed-circle diameter
# is R*sqrt(3) ≈ 93.5 for R=54, so the IE logo at 70 takes ~75% with padding.
LOGO_GROUPS = [
    ("IE",           "inference-endpoints.svg", None,           [(0, 0)],                   70.0),
    ("SGLang",       "engine-3.svg",            "SGL",          [(-2, -2), (-1, -2)],       30.0),
    ("vLLM",         "engine-2.svg",            "vLLM",         [(1, -2),  (2, -2)],        30.0),
    ("LlamaCpp",     "engine-4.svg",            "LLaMA",        [(-3, 0),  (-2, 0)],        30.0),
    ("TGI",          "engine-5.svg",            "TGI",          [(2, 0),   (3, 0)],         30.0),
    ("Transformers", "engine-1.svg",            "Transformers", [(-1, 2),  (0, 2), (1, 2)], 30.0),
]


def _tile_center(i: int, j: int, R: float) -> tuple[float, float]:
    from math import sqrt
    s3 = sqrt(3)
    x_offset = (R * s3 / 2) if (j % 2) else 0.0   # offset for odd rows
    return (i * R * s3 + x_offset, j * 1.5 * R)


def build_cube_pattern_svg(
    R: float = 54.0,
    line_width: float = 1.0,
    dot_radius: float = 2.0,
    viewbox_w: float = 800.0,
    viewbox_h: float = 440.0,
) -> str:
    """Repeating SVG pattern of isometric 3D cubes — pointy-top hexagonal cells
    with three internal lines from center to alternating vertices (the visible
    cube edges) and a dot at every vertex.

    R is tuned for the engines panel size so ~5 rows of cubes are visible.
    The viewBox is centered at (0, 0) and the pattern is shifted so a hex1
    center (a connection-point dot) lands exactly on viewBox (0, 0). Combined
    with preserveAspectRatio="xMidYMid slice", that dot stays centered in the
    panel regardless of resize.

    Pure decoration, aria-hidden."""
    from math import sqrt
    s3 = sqrt(3)
    pw = R * s3           # pattern cell width
    ph = R * 3            # pattern cell height
    color = CUBE_PATTERN_COLOR

    # Hex1 sits fully inside the cell. Hex2 straddles a cell boundary in
    # honeycomb tilings — to avoid missing segments where SVG clips at the
    # cell edge, we draw hex2 at ALL FOUR equivalent positions so every
    # neighboring tile contributes its visible portion.
    centers = [
        (R * s3 / 2, R),       # hex1 — fully inside
        (0.0, 5 * R / 2),      # hex2 at LEFT edge, BOTTOM-overflow (right-top half in this cell)
        (pw,  5 * R / 2),      # hex2 at RIGHT edge, BOTTOM-overflow (left-top half in this cell)
        (0.0, -R / 2),         # hex2 at LEFT edge, TOP-overflow (right-bottom quarter in this cell)
        (pw,  -R / 2),         # hex2 at RIGHT edge, TOP-overflow (left-bottom quarter in this cell)
    ]

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

    # Translate the pattern so hex1's center (LOCAL R*s3/2, R) lands on user
    # coordinate (0, 0) — which sits at the viewBox center, which (via slice)
    # is the panel center.
    px_shift = -R * s3 / 2
    py_shift = -R

    vb_x = -viewbox_w / 2
    vb_y = -viewbox_h / 2

    return f'''<svg xmlns="http://www.w3.org/2000/svg" class="absolute inset-0 w-full h-full" viewBox="{vb_x:.3f} {vb_y:.3f} {viewbox_w:.3f} {viewbox_h:.3f}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <pattern id="cube-grid" patternUnits="userSpaceOnUse" width="{pw:.3f}" height="{ph:.3f}" patternTransform="translate({px_shift:.3f} {py_shift:.3f})">
      <path d="{path_d}" stroke="{color}" stroke-width="{line_width}" fill="none"/>
      {dots}
    </pattern>
  </defs>
  <rect x="{vb_x:.3f}" y="{vb_y:.3f}" width="{viewbox_w:.3f}" height="{viewbox_h:.3f}" fill="url(#cube-grid)"/>
</svg>'''


def build_engines_panel_svg(
    R: float = LOGO_TILE_R,
    viewbox_w: float = VIEWBOX_W,
    viewbox_h: float = VIEWBOX_H,
    line_width: float = 1.0,
    dot_radius: float = 2.0,
    font_size: float = 24.0,
    text_gap: float = 6.0,
    icon_y_adjust: float = -2.0,    # nudge icons up a few units so they
                                    # visually align with the monospace
                                    # cap-text mid-line, not its em-box mid.
                                    # Applied to logos with text only.
) -> str:
    """Cube-pattern panel with engine logos + IBM Plex Mono labels.

    Renders the cube grid hex-by-hex (rather than via SVG <pattern>) so
    individual tiles can be omitted where logos sit. Each engine takes 2
    hex tiles (icon + text); "Transformers" takes 3 because the label is
    longer. The Inference Endpoints logo sits in the center tile, icon
    only. Lines/dots are drawn only for hexes NOT taken by a logo."""
    from math import sqrt
    s3 = sqrt(3)
    color = CUBE_PATTERN_COLOR

    # Tiles occupied by logo content — pattern is suppressed on these.
    taken: set[tuple[int, int]] = set()
    for entry in LOGO_GROUPS:
        for t in entry[3]:
            taken.add(t)

    # Visible (i, j) bounds (with a margin so partially-clipped hexes still
    # contribute their stroke segments along the panel edge).
    j_max = int(viewbox_h / 2 / (1.5 * R)) + 2
    i_max = int(viewbox_w / 2 / (R * s3)) + 2

    hex_paths: list[str] = []
    dot_marks: list[str] = []

    for j in range(-j_max, j_max + 1):
        for i in range(-i_max, i_max + 1):
            if (i, j) in taken:
                continue
            cx, cy = _tile_center(i, j, R)
            verts = [
                (cx,               cy - R),
                (cx + R * s3 / 2,  cy - R / 2),
                (cx + R * s3 / 2,  cy + R / 2),
                (cx,               cy + R),
                (cx - R * s3 / 2,  cy + R / 2),
                (cx - R * s3 / 2,  cy - R / 2),
            ]
            # Hex outline (6 edges) + 3 internal Y-lines from center to
            # top / bottom-right / bottom-left vertices (the visible cube
            # corner edges).
            outline = (
                f"M {verts[0][0]:.2f} {verts[0][1]:.2f} "
                + " ".join(f"L {x:.2f} {y:.2f}" for x, y in verts[1:])
                + " Z"
            )
            y_arms = (
                f" M {cx:.2f} {cy:.2f} L {verts[0][0]:.2f} {verts[0][1]:.2f}"
                f" M {cx:.2f} {cy:.2f} L {verts[2][0]:.2f} {verts[2][1]:.2f}"
                f" M {cx:.2f} {cy:.2f} L {verts[4][0]:.2f} {verts[4][1]:.2f}"
            )
            hex_paths.append(outline + y_arms)
            # 7 dots per hex (center + 6 vertices). Dots at shared vertices
            # are drawn by multiple hexes but overlap at the same coords.
            for vx, vy in verts + [(cx, cy)]:
                dot_marks.append(f'<circle cx="{vx:.2f}" cy="{vy:.2f}" r="{dot_radius}"/>')

    # Combined stroke path for all hex outlines + Y-arms (much smaller
    # output than one <path> per hex).
    combined_path = " ".join(hex_paths)

    # Logo elements
    # IBM Plex Mono advance width is ~0.6 of font-size (600 units in 1000-unit em).
    MONO_CHAR_WIDTH_RATIO = 0.6
    logo_html: list[str] = []
    for name, icon_file, text, tiles, this_icon_size in LOGO_GROUPS:
        # Geometric center of all tiles this logo occupies — combo gets
        # centered here so the icon+text reads as a balanced unit.
        tile_centers = [_tile_center(*t, R) for t in tiles]
        combo_cx = sum(cx for cx, _ in tile_centers) / len(tile_centers)
        combo_cy = sum(cy for _, cy in tile_centers) / len(tile_centers)
        nudge = icon_y_adjust if text else 0.0

        if text:
            text_width = len(text) * font_size * MONO_CHAR_WIDTH_RATIO
            combo_width = this_icon_size + text_gap + text_width
            icon_left = combo_cx - combo_width / 2
            text_x = icon_left + this_icon_size + text_gap
        else:
            icon_left = combo_cx - this_icon_size / 2

        iy = combo_cy - this_icon_size / 2 + nudge
        logo_html.append(
            f'<image href="assets/logos/{icon_file}" x="{icon_left:.2f}" y="{iy:.2f}" '
            f'width="{this_icon_size}" height="{this_icon_size}" preserveAspectRatio="xMidYMid meet"/>'
        )
        if text:
            logo_html.append(
                f'<text x="{text_x:.2f}" y="{combo_cy:.2f}" '
                f'font-family="\'IBM Plex Mono\', monospace" font-weight="400" '
                f'font-size="{font_size}" fill="{LOGO_TEXT_COLOR}" '
                f'dominant-baseline="middle" text-anchor="start">{text}</text>'
            )

    # Engine→IE shooting-line animations (with vertex flashes)
    anim_defs, anim_body = _build_engine_animations(R, dot_radius=dot_radius)

    vb_x = -viewbox_w / 2
    vb_y = -viewbox_h / 2

    return f'''<svg xmlns="http://www.w3.org/2000/svg" class="absolute inset-0 w-full h-full" viewBox="{vb_x:.2f} {vb_y:.2f} {viewbox_w:.2f} {viewbox_h:.2f}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
<defs>{anim_defs}</defs>
<g fill="none" stroke="{color}" stroke-width="{line_width}"><path d="{combined_path}"/></g>
<g fill="{color}">{"".join(dot_marks)}</g>
{"".join(logo_html)}
{anim_body}
</svg>'''


def ensure_mono_light_font(html: str) -> str:
    """Add weight 300 to the IBM Plex Mono Google Fonts request so the
    engine labels can render in light weight."""
    return html.replace(
        "family=IBM+Plex+Mono:wght@400;600;700",
        "family=IBM+Plex+Mono:wght@300;400;600;700",
    )


def inject_engine_cube_pattern(html: str) -> str:
    """Fill the engines section's right column with the cube pattern panel
    (hex grid + 6 engine logos + IBM Plex Mono labels)."""
    target = '<div class="relative z-1 grid bg-gray-50 lg:col-span-3"></div>'
    if target not in html:
        return html
    pattern_svg = build_engines_panel_svg()
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
    html = ensure_mono_light_font(html)
    html = inject_engine_cube_pattern(html)

    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} ({len(html):,} chars)")


if __name__ == "__main__":
    main()
