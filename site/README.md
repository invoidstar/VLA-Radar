# Site source

This directory contains the human-authored static website source. GitHub Pages does not publish this directory directly: `scripts/build/stage_site.py` combines `site/` with generated `data/` into a disposable public root. Public routes therefore remain unchanged.
