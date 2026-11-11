# Paper Deep Reading · public content workflow

VLA-Radar v3.1 introduces a standalone, static, **license-bounded** reading mode. Paper IDs remain canonical: SLA is \`p148\`. The original user-supplied full bilingual annotated PDF-to-HTML example is **not shipped** with this public repository. It was used as an editorial/interaction reference, not as permission to redistribute a paper, PDF page crop, or full paragraph-by-paragraph translation.

## Public content contract

- \`catalog/close-readings/index.json\` is the listing manifest.
- \`catalog/close-readings/p148.json\` is the section- and paragraph-ID-level *original editorial analysis* source. Every unit records a paper/source version and PDF page number; English keyword phrases are **index terminology, not claimed as verbatim original paragraphs**.
- Only \`visibility=public-commentary-only\` and \`originalTextStatus=omitted-pending-permission\` are admitted by the v3.1 validator. The public reader has no full English paper paragraphs, no full paragraph translations, no paper PDF binary or screenshots, and no embedded base64 figures. Reusing full text or images requires a separate, documented permission/licensing review and deliberately designed public schema update.
- The original PDF remains at arXiv and is opened via source-position links. The paper's bibliographic identity, benchmark result evidence and experiments continue to live in existing \`catalog/papers/p148.json\` and \`catalog/results/*\`.
- Do not import unpublished, private research data, chats or user local reading history into the public repository.

## Development

1. Add a \`catalog/close-readings/pNNN.json\`, preserving its stable ID, sourced chapter order, unique \`P001\`-style units and paper's actual \`sourceVersion\`. Ensure the citation year and source page correspond to what was actually reviewed. If the full source was not read, publish a partial reading with clearly limited coverage, not fabricated source passages.
2. Register the matching metadata entry in \`catalog/close-readings/index.json\`; verify its link/sectionCount/unitCount and source version.
3. Run \`python scripts/build/build_catalog.py\` and \`python scripts/validate/validate_all.py\`. The generated \`data/close-readings/*.json\` are derived, not edited by hand.
4. For new paper routes, add a valid \`site/close-reading/pNNN/index.html\` that uses the shared static reader. Register it in \`scripts/build/stage_site.py\`. Existing browser checks assert p148; extend them for additional pages.
5. Check HTTP/browser behavior, mobile and print output, data payload size, permission status, source/evidence links and browser state. The new \`vla-radar.close-reading.v1\` preference key never mutates the existing \`vla-radar.reading.v1\` local reading state.
6. Publish through a normal PR exact-head \`quality\` gate, then verify the same main commit's Pages staging, deployment and production smoke. GitHub Pages needs no database or network request to render a published reading.

## Architecture

The page listing is available at \`/VLA-Radar/close-reading/\`, the standalone reader at \`/VLA-Radar/close-reading/p148/\`. The home sidebar links to the catalog, and the p148 paper detail offers a deep-reading link. The first page and main paper library do not eagerly fetch the content shard; only the reading page loads \`/data/close-readings/p148.json\`. This keeps normal library startup unchanged.

\`site/close-reading/reading.css\` and \`reader.js\` are reused independent presentation assets. Text is HTML-escaped before rendering, no user-supplied HTML is injected, no separate font CDN is required and no cross-device personal state is stored.
