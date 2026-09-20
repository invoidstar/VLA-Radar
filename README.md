# VLA-Radar

<p align="center">
  <strong>Evidence-linked research radar for Vision-Language-Action, World Action Models, and robot foundation models.</strong>
</p>

<p align="center">
  从论文发现、深度阅读，到 Benchmark 对齐、结果比较与证据追溯。<br>
  一个面向 VLA / WAM / 机器人基础模型研究的开放、静态、持续维护的研究雷达。
</p>

<p align="center">
  <a href="https://invoidstar.github.io/VLA-Radar/"><strong>🌐 Live Site</strong></a>
  ·
  <a href="https://github.com/invoidstar/VLA-Radar/actions/workflows/site.yml">CI / Pages</a>
  ·
  <a href="MAINTENANCE.md">Maintenance</a>
  ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

<p align="center">
  <img alt="Validate and deploy VLA Radar" src="https://github.com/invoidstar/VLA-Radar/actions/workflows/site.yml/badge.svg">
  <img alt="Version" src="https://img.shields.io/badge/version-V3.0-5964a8">
  <img alt="Static Site" src="https://img.shields.io/badge/site-static%20%2B%20GitHub%20Pages-6f7893">
  <img alt="Privacy" src="https://img.shields.io/badge/reading%20data-local--only-6d8b73">
</p>

---

## What is VLA-Radar?

**VLA-Radar** is a research-oriented reading and evidence workspace for the rapidly evolving VLA ecosystem.

It is designed around a simple idea:

> **Do not stop at collecting paper titles. Follow the evidence from paper → evaluation protocol → reported result → source.**

The project tracks public work around:

- Vision-Language-Action models
- Vision / Video-Action models
- World Action Models and robot world models
- Robot foundation models
- Pre-training / post-training / RL
- Memory and long-horizon control
- Spatial / 3D / geometry-aware policies
- Action representation and tokenization
- Inference / training efficiency
- Benchmarks, datasets and evaluation methodology

VLA-Radar is **not** an official leaderboard and does not collapse incompatible evaluations into a universal score.

---

## V3.0 Snapshot

Current public catalog:

| Layer | Scale |
|---|---:|
| Papers | **98** |
| Benchmarks | **61** |
| Evaluation Settings | **194** |
| Canonical Tracks | **286** |
| Reported Results | **1063** |

V3.0 marks the transition from a paper-reading website to a stable **research radar** with a unified evidence model, Benchmark discovery system, workspace tools, and a repeatable maintenance pipeline.

---

## Core Features

### 📚 Paper Library

- Structured paper cards and deep reading notes
- Search by title, team, method, topic, findings and keywords
- Topic, venue, time and reading-status filters
- Publication timeline with first-public / arXiv / acceptance / publication distinctions
- Paper detail pages with:
  - reading notes
  - lifecycle history
  - benchmark evidence
  - source links and locators

### 🧭 Research Discovery

- Research-topic overview
- Timeline view
- **Embodied AI Weekly / 具身智能周报**
- Update center for actual catalog changes
- Global command search

### 📊 Evidence-linked Benchmark Explorer

V3.0 uses the following default hierarchy:

```text
Benchmark
  ↓
Evaluation Setting
  ↓
Result Report
```

where:

> **Evaluation Setting = Evaluation Protocol only**

Training data, recipe, source paper, base model and checkpoint do **not** define the Setting identity.

Each result report preserves:

```text
Method
Score
Training Data
Source Paper
Recipe / Evidence
```

This keeps the evaluation question stable while still exposing why two reports of the same method may produce different scores.

### 🔎 Benchmark Search & Taxonomy

All 61 Benchmarks are discoverable through:

**Search**

- Benchmark / Dataset name
- Evaluation Setting
- task scope
- split
- metric
- score columns

**Focus**

- General Manipulation
- Long-Horizon & Memory
- Generalization & Robustness
- Dexterous & Contact-Rich
- Language, Planning & Compositionality
- Efficiency & Deployment

**Environment**

- Simulation
- Real Robot
- Mixed / Cross-Environment

**Tags**

Examples include:

- Household / Kitchen
- Tabletop
- Industrial / Assembly
- Bimanual / Dual-arm
- Tactile
- Long-horizon
- Memory
- Multi-task
- Robustness / OOD
- Sim-to-Real
- Latency / Efficiency
- Language / Compositionality

Search, Focus, Environment and Tags can be combined and are preserved in shareable URLs.

### 🧪 Advanced Track Analysis

The exact canonical track remains available as the evidence-level view:

- original protocol
- arbitrary score-column sorting
- metric direction
- bar charts
- time–score scatter
- source / verification dates
- CSV export
- exact result IDs and source locators

No missing value is silently converted to zero.

### 🛠 Research Workspace

- 2–4 paper comparison
- citation / Markdown / CSV export
- focused reader view
- evidence coverage map
- update stream
- My Radar
- local reading list

Personal reading state, follows and filters stay in the browser and are never written into the public catalog.

---

## Benchmark Data Model

The public benchmark layer is intentionally split into three levels.

### 1. Benchmark

A dataset or evaluation family, such as:

`RoboTwin`, `LIBERO`, `RoboCasa`, `RLBench`, `CALVIN`, `RoboDojo`, `SimplerEnv`, etc.

Benchmark-level discovery metadata lives in:

```text
catalog/benchmark-taxonomy.json
```

### 2. Evaluation Setting

A generated comparison layer answering:

> Are these reports evaluating the same benchmark question?

The Setting identity may include:

- dataset / benchmark
- task set
- evaluation split / condition
- metric
- unit and optimization direction
- genuine evaluation-context differences

It does **not** split merely because of:

- training dataset
- demonstration count
- SFT vs co-training
- batch size / steps / learning rate
- architecture / base model
- checkpoint
- source paper

### 3. Canonical Track / Result

The precise evidence layer.

```text
catalog/benchmarks.json
catalog/results/r-*.json
```

Tracks preserve the source-defined protocol and result records preserve source paper, value, locator, training description and verification metadata.

---

## Repository Structure

```text
VLA-Radar/
├── site/                       # Static frontend
│   ├── index.html
│   ├── js/
│   │   ├── core/
│   │   ├── components/
│   │   └── features/
│   └── styles/
│
├── catalog/                    # Canonical public research data
│   ├── papers/                 # One paper per source file
│   ├── results/                # Evidence-linked result records
│   ├── benchmarks.json         # Canonical evaluation tracks
│   ├── benchmark-taxonomy.json # Focus / Environment / Tags
│   ├── bibliography.json
│   └── manifest.json
│
├── data/                       # Deterministic generated artifacts
│   ├── details/
│   ├── boards/
│   ├── settings/
│   ├── paper-results/
│   └── hashed indexes
│
├── scripts/
│   ├── build/
│   ├── validate/
│   ├── browser/
│   ├── discovery/
│   ├── maintenance/
│   └── migrations/
│
├── tests/
├── maintenance/                # Policies, state and release audits
├── MAINTENANCE.md
└── AGENTS.md
```

**Canonical data lives in `catalog/`. Generated `data/` files should not be edited manually.**

---

## Quick Start

Requirements:

- Python 3.10+
- Node.js 18+
- no database
- no model API key
- no frontend framework build step

Build and validate:

```bash
python scripts/build/build_catalog.py
python scripts/validate/validate_all.py
```

Stage the public site:

```bash
python scripts/build/stage_site.py --output _site
python -m http.server 8080 -d _site
```

Then open:

```text
http://localhost:8080
```

The site is designed for static hosting and is deployed through GitHub Pages.

---

## Adding or Updating Research Content

### Paper

Edit:

```text
catalog/papers/pNNN.json
```

### Benchmark protocol

Edit:

```text
catalog/benchmarks.json
```

### Result evidence

Edit:

```text
catalog/results/r-*.json
```

### Benchmark classification

Edit:

```text
catalog/benchmark-taxonomy.json
```

Every real Benchmark must have:

- exactly one Focus
- exactly one Environment
- controlled Tags

After canonical changes:

```bash
python scripts/build/build_catalog.py
python scripts/validate/validate_all.py
```

The validator checks schema, deterministic generation, evidence constraints, taxonomy coverage, performance budgets, Node regressions and browser-facing invariants.

---

## Evidence Principles

VLA-Radar follows several non-negotiable rules.

### 1. Protocol before ranking

Results are only compared inside a clearly defined evaluation context.

### 2. Missing is not zero

Unreported values remain missing.

### 3. Same method ≠ same report

The same method can appear multiple times when different papers, training data or recipes report different outcomes.

### 4. Source attribution stays visible

Author-reported methods, reported baselines and independent reproductions are not silently treated as equivalent evidence.

### 5. No automatic “best score” representative

VLA-Radar does not deduplicate a method by keeping its highest reported number.

### 6. Metadata and scientific verification are different

A successful schema / CI check proves structural consistency, not scientific truth. Quantitative claims still require source review.

---

## Privacy

VLA-Radar is a static public website.

Personal state such as:

- saved papers
- reading status
- follows
- reading position
- local filters and preferences

stays in the user's browser.

The public repository does not store personal reading history or analytics-derived user profiles.

---

## Maintenance

VLA-Radar is currently in **V3 stable maintenance mode**.

The default strategy is no longer to continuously add product features. Weekly maintenance focuses on:

1. public VLA / WAM paper discovery
2. full-text reading and source verification
3. publication-status updates
4. benchmark / result evidence extraction
5. Evaluation Setting consistency
6. Benchmark taxonomy coverage
7. Embodied AI Weekly
8. source-health rotation
9. deterministic build and validation
10. Chromium regression tests
11. GitHub Pages deployment and branch housekeeping

See:

- [MAINTENANCE.md](MAINTENANCE.md) — data semantics and maintenance workflow
- [AGENTS.md](AGENTS.md) — automation and public-data boundaries
- [CHANGELOG.md](CHANGELOG.md) — project evolution

---

## Project Status

**V3.0 · Stable Research Radar**

The project has completed its main information-architecture phase.

Future engineering work is expected only when there is a concrete need such as:

- a real usability problem
- a measurable performance bottleneck
- a reliability issue
- a security / compatibility requirement

Otherwise, development effort goes into **better evidence, broader coverage and more reliable maintenance**.

---

## Scope & Disclaimer

VLA-Radar is an independent research reading and evidence project.

- It is not an official leaderboard for any benchmark.
- It does not claim exhaustive coverage of the VLA field.
- Reported numbers belong to their cited sources and evaluation conditions.
- Cross-paper comparison may still differ in training data, model scale, compute, checkpoint selection or other recipe details even when the Evaluation Setting is aligned.
- Public sources only; unknown information is left unknown rather than guessed.

---

<p align="center">
  <strong>READ PAPERS. FOLLOW EVIDENCE.</strong>
</p>
