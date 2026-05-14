# Inference Endpoints — design handoff (Svelte 5)

A drop-in Svelte 5 / Tailwind v4 implementation of three landing-page sections:
Features, Engines (with the custom cube-grid + animated traveling lines), and
Pricing. Engines is the unique design contribution; Features and Pricing are
included as reference markup in case they're useful.

Live preview of the same components built standalone:
**https://chuntelee.github.io/inference-endpoints-landing-cube/**

## Contents

```
handoff/
├── README.md                     (this file)
├── theme.css                     Tailwind @theme tokens to merge into app.css
├── components/
│   ├── EnginesPanel.svelte       Cube grid + 6 engine logos + traveling-line animations
│   └── page-sections.svelte      Features + Engines + Pricing markup, imports EnginesPanel
└── static/
    ├── logo-endpoints.svg        (used in header — optional, only if you want my header markup)
    └── logos/
        ├── inference-endpoints.svg   center IE chevron (used by EnginesPanel)
        ├── engine-1.svg              HF Transformers smiley
        ├── engine-2.svg              vLLM (V chevron)
        ├── engine-3.svg              SGLang (node graph)
        ├── engine-4.svg              llama.cpp (orange C++)
        └── engine-5.svg              TGI (blue diamond)
```

## Requirements

Your project should be on (or compatible with):

- **Svelte 5** — the components use runes (`$props()`) and `{@render}`
- **SvelteKit 2** — `EnginesPanel.svelte` imports `$app/paths` for the base
  path. If you don't use SvelteKit, replace the import with a plain string
  prefix and adjust the `<image href>` paths.
- **Tailwind v4** — the markup uses v4 utilities (`size-5`, `bg-amber-400/10`,
  the new `divide-x` model, etc.) and `@theme` directive syntax. The v3
  config-file approach will not work without rewrites.
- **Google Fonts** — Source Sans Pro and IBM Plex Mono with weight 400.
  See `theme.css` for the `<link>` tags.

## Integration steps

1. **Theme** — merge the contents of `theme.css` into your app's main CSS
   (the one with `@import 'tailwindcss';`). Add the Google Fonts `<link>`
   tags to your `app.html` or layout head if not already present.

2. **Static assets** — copy `static/logos/*` and `static/logo-endpoints.svg`
   into your project's `static/` folder (or wherever SvelteKit serves
   public assets from). If you put them elsewhere, update the paths inside
   `EnginesPanel.svelte` (search for `{base}/logos/`).

3. **Components** — drop `EnginesPanel.svelte` into `src/lib/` (or wherever
   your component library lives). Adjust the import in `page-sections.svelte`
   from `./EnginesPanel.svelte` to the matching path in your project.

4. **Page markup** — use `page-sections.svelte` as a reference. You probably
   won't want it as one big file — split the three `<section>` blocks into
   your existing layout / route components. The key piece is the Engines
   section, which wraps `<EnginesPanel />` in the right column of the
   2-column grid.

## How the animation works

`EnginesPanel.svelte` renders a single inline SVG with everything baked in:

- **Cube grid** — pure SVG paths, every hex outline is a separate sub-path so
  the dashes (if you ever turn them on) don't interlock.
- **Logos** — `<image href="...">` with paths under `static/logos/`.
- **Traveling lines** — pure SMIL (`<animate>` on `stroke-dasharray` and
  `stroke-dashoffset`). The line grows from 0 at the source vertex, slides
  along the path bending naturally through every waypoint, then shrinks
  into the IE center dot. No JavaScript involved in the animation.
- **Vertex flashes** — each connection point the line passes through has a
  paired `<circle>` whose `opacity` animates briefly with the line.
- **Edge fade** — four linear gradient rects at the panel borders so the
  pattern bleeds into the page background.

Because the SVG and animations are entirely declarative and prerendered, the
animation starts on the FIRST PAINT of the page — before any JS hydration.

## Tuning the engines panel

Everything visual is at the top of `EnginesPanel.svelte` in plain constants.
Common adjustments:

| Constant | What it controls |
|---|---|
| `R` | Hex tile radius. Whole panel scales with this. |
| `ANIM_COLOR` | Pink/red of the traveling lines (defaults to IE brand `#FF2A4A`). |
| `LOGO_GROUPS[].tiles` | Which hex cells each logo occupies. Move logos by changing the `(i, j)` coordinates. |
| `LOGO_GROUPS[].iconSize` | Icon size in user units (IE is 70, engines are 30). |
| Inside `buildAnimations()`: `CYCLE` | Total animation cycle (seconds). Larger = slower repeat. |
| Inside `buildAnimations()`: `SPEED` | Line traversal speed (units/sec). Larger = faster. |
| Inside `buildAnimations()`: `TRAIL` | Line length in user units. |
| `TIME_SLOT` | Permutation that decides which path takes which begin-time slot — controls how lines are distributed around the panel over time. |

## Notes / known limits

- The `Catalog` link in my version of the header is a placeholder href and
  will 404. Wire it to your real route.
- The Pricing section's "See Instance Pricing" and "Request a Quote" links go
  to public Hugging Face URLs.
- The 5 engine logos came from the design file as `Frame 554..558.svg` and
  were renamed `engine-1..5.svg`. The mapping (in order): Transformers /
  vLLM / SGLang / llama.cpp / TGI.
- All animations respect `prefers-reduced-motion` only if you wrap the
  `<animate>` tags in a media query — currently they always run. Easy to add
  if your site disables motion.
