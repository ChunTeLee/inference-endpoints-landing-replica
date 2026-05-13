# Inference Endpoints Landing — Replica

Static replica of the Hugging Face Inference Endpoints landing page, with a custom animated engine-orbit graphic in the Engines section.

## Live preview

GitHub Pages serves `index.html` from the repo root.

## What's here

- `index.html` — self-contained replica
- `assets/` — mirrored images, favicons, and engine logos
- `page-source.html` — raw SSR fetch of the original page (input to the build)
- `build.py` — pipeline that strips the SvelteKit hydration script, absolutizes URLs, localizes assets, and injects the engine-orbit SVG

## Rebuild

```
python build.py
```

## Notes

- Nav links (`/`, `/catalog`, `/new?...`) point at the original SvelteKit routes and won't resolve from this static host — they're dead clicks by design.
- The engine-orbit SVG (two counter-rotating rings + static decorative ripple rings) is generated in `build.py::build_orbit_svg`.
