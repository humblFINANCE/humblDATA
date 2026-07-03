# AGENTS.md - humblDATA

Python data library for the humblFINANCE ecosystem. Implements the quantitative/technical/fundamental models (humblCHANNEL, humblCOMPASS, humblMOMENTUM, humblPORTFOLIO, etc.) using the CCCC architecture pattern. Published to PyPI as `humbldata` and consumed by `humblAPI`.

## Ecosystem

This is one of three sibling repos (all under `~/github/humblFINANCE-org/`):

| Repo | What it is | Depends on |
|---|---|---|
| **humblDATA** (this repo) | Python analytics library, published to PyPI | OpenBB API, Redis, Alpaca, NixTla |
| `humblAPI` | FastAPI service on Render, wraps this library | `humbldata` (PyPI pin) |
| `humblFINANCE` | Next.js app on Vercel + Supabase | Calls `humblAPI` over HTTP |

Data flows: `humblDATA` (library) -> `humblAPI` (HTTP service) -> `humblFINANCE` (frontend). This repo has no HTTP surface of its own; humblAPI is the only consumer.

**Important**: bumping a version here does NOT automatically update humblAPI. humblAPI pins `humbldata>=1.22.1` in its `pyproject.toml` - after publishing a new release here, go bump that pin in humblAPI and redeploy.

**OpenBB API hosting**: `humbldata` does not use the `openbb` Python package - it calls a self-hosted OpenBB Platform API instance over HTTP via `core/utils/openbb_api_client.py`. In production that instance runs on **DigitalOcean App Platform** (`openbbapi-y9f49.ondigitalocean.app`), fronted by Cloudflare under the custom domain `https://data.humblfinance.io` (`OPENBB_API_PROD_URL`). By default `OPENBB_API_DEV_URL` also points at this same prod instance - there is no local OpenBB in the default dev stack. If you're running the full ecosystem via `humblWORKSPACE`, use `pixi run dev:local-openbb` to run OpenBB locally (Docker, port `6900`, via [jjfantini/openbbAPI](https://github.com/jjfantini/openbbAPI)) instead - only needed when testing an OpenBB version bump or provider credentials.

## Stack

- **Language**: Python `>=3.11,<3.13`
- **Build backend**: `hatchling` (PEP 621 `pyproject.toml`, not a `[tool.poetry]` table)
- **Package manager**: `uv` (canonical lockfile is `uv.lock`). Some docs/CI still say Poetry - `uv` is the source of truth for install/build/publish.
- **Task runner**: `poethepoet` (`poe <task>`)
- **Core libs**: Polars, Pydantic, Pandera, aiohttp, aiocache, python-redis-cache, scikit-learn, plotly. OpenBB is **not** a pip dependency - it's called over HTTP via `core/utils/openbb_api_client.py`.
- **Docs**: MkDocs Material, published to `https://humblfinance.github.io/humblDATA/`
- **Quality**: Ruff (line-length 80, numpy docstrings), Mypy (`strict = true`), pre-commit, Commitizen (`cz_gitmoji`), Cruft (template sync)

## Architecture: CCCC pattern

```
src/humbldata/
  core/        # shared: standard_models, utils (env, cache, logger, openbb client), backtesting
  toolbox/     # Context: technical/ fundamental/ quantitative/ (Categories) -> humbl_channel/ humbl_compass/ ... (Commands)
  portfolio/   # Context: analytics/ (watchlist), strategies/ (backtests)
```

Every command follows `Controller -> QueryParams -> Fetcher -> Data`, with shared models in `core/standard_models/`. Scaffold a new command with `poe add_command`. See `.cursor/rules/add-query-param.mdc` and `docs/code_design/cccc_method.md` for details.

## Run locally

```bash
# optional: micromamba env (per docs/getting_started/development_setup.md)
micromamba activate ./menv

# install deps (uv.lock is canonical)
uv sync

# run tests (unit + integration split under tests/)
poe test              # coverage run -> report -> xml
pytest -m "not slow"  # direct, markers: integration, slow

# lint (ruff + mypy via pre-commit, plus safety check)
poe lint

# serve docs locally
mkdocs serve

# scaffold a new CCCC command
poe add_command

# notebooks
poe lab
```

Environment variables load from a root `.env` (no `.env.example` is committed - create one). Key vars, from `src/humbldata/core/utils/env.py`:

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | `development` (default) or `production` |
| `OBB_PAT`, `OBB_LOGGED_IN` | OpenBB Personal Access Token / login flag |
| `OPENBB_API_PROD_URL`, `OPENBB_API_DEV_URL`, `OPENBB_API_PREFIX` | OpenBB API base URLs (default prefix `/api/v1`). Prod = self-hosted OpenBB Platform on DigitalOcean App Platform, at `https://data.humblfinance.io` |
| `ALPACA_API_KEY`, `ALPACA_API_SECRET` | Alpaca |
| `REDIS_URL`, `REDIS_REST_API_URL`, `REDIS_API_TOKEN`, `REDIS_REST_API_READ_ONLY_TOKEN` | Redis / Upstash |
| `NIXTLA_API_KEY` | TimeGPT |
| `LOGGER_LEVEL` | DEBUG/INFO/WARNING/ERROR/CRITICAL |

## Release and publish (external tools: GitHub Actions, Commitizen, PyPI, GitHub Pages)

There is no manual "deploy" step - releases and docs publish automatically from CI:

1. Push commits to `develop` (integration) or `main` (release; gitmoji conventional commits, see below) -> `.github/workflows/test.yml` runs pytest on push to both branches.
2. `.github/workflows/bump.yml` runs Commitizen on push to `main` only, bumps `version` in `pyproject.toml`, updates `CHANGELOG.md`, tags `v$version`, and creates a GitHub release. Skips if the triggering commit message already contains `bump(release)`.
3. That tag push triggers, in parallel:
   - `.github/workflows/publish.yml` - `uv build` + `uv publish` to PyPI (`POETRY_PYPI_TOKEN_PYPI` secret). Also triggers on push to a `release` branch.
   - `.github/workflows/docs.yml` - `uv run mkdocs gh-deploy --force` to GitHub Pages.

To cut a release manually instead: `cz bump` locally, then push the tag.

## Commit convention

Gitmoji conventional commits (`.cz-config.js` / `.pre-commit-config.yaml` runs `cz check`), format `<type>(<scope>): <subject>`. Allowed types: `feat`, `fix`, `hotfix`, `chore`, `refactor`, `WIP`, `docs`, `perf`, `style`, `build`, `ci`, `test`, `revert`, plus `dep-add` / `dep-rm` / `boom`.

## Known quirks (don't be surprised)

- `poetry.lock` does not exist; `uv.lock` is canonical, but `test.yml` CI and pre-commit's `poetry-check` still assume Poetry.
- `.devcontainer/` and a `Dockerfile` are referenced in docs but not present in the repo.
- `src/humbldata/cli.py` exists but has no `[project.scripts]` entry point - it is not installed as a CLI.

## Cursor Cloud specific instructions

The startup update script already runs `uv sync --all-groups` here, so deps are installed. Notes:

- **`.env` is required but not committed.** A minimal dev `.env` at the repo root is enough: `ENVIRONMENT=development`, `OPENBB_API_DEV_URL`/`OPENBB_API_PROD_URL=https://data.humblfinance.io`, `OPENBB_API_PREFIX=/api/v1`, `REDIS_URL=redis://localhost:6379`. All `Env` properties have safe defaults, so `import humbldata` works without it, but integration/data paths call the hosted OpenBB API (`data.humblfinance.io`) and need network.
- **Use `--all-groups`, not plain `uv sync`.** The test/lint tooling (pytest-asyncio, ruff, mypy, pre-commit, safety) lives in non-default dependency groups; plain `uv sync` omits them and pytest then fails collection with `'asyncio' not found in markers` under `--strict-markers`.
- **The test suite has ~70 pre-existing failures that CI tolerates** (`test.yml` marks `poe test` `continue-on-error: true`). Notably: some files do `from src.humbldata...` (breaks under `--import-mode=importlib`), and several assertions/doctests are stale (e.g. plotly `heatmapgl` deprecation). Don't assume a red suite is your fault - run a targeted subset (e.g. `uv run pytest tests/test_import.py`) to sanity-check the harness.
- Lint tooling runs via `uv run ruff check ...` and `uv run mypy ...`; `poe lint` also runs `pre-commit` (downloads hook envs on first run) and `safety`.
