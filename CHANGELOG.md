## v1.0.10 (2024-03-14)

### 🐛🚑️ Fixes

- **ToolboxData**: added alias `dt` for `datetime` to use  `date` type in fieldinfo

### ✅🤡🧪 Tests

- **mandelbrpt_channel_integration**: added initial mandelbrot_channel integration tests

## v1.0.9 (2024-03-13)

### 🐛🚑️ Fixes

- **docs.yml**: `git fetch gh-pages` branch before `mike deploy`

## v1.0.8 (2024-03-13)

### 🐛🚑️ Fixes

- **docs**: added correct syntax for `mike deploy`

## v1.0.7 (2024-03-13)

### 🐛🚑️ Fixes

- **test**: esting doc building with a new tag push from `bump.yml`

## v1.0.6 (2024-03-13)

### 🐛🚑️ Fixes

- **mandelbrot_channel**: renamed `recent_price` --> `close`

## v1.0.5 (2024-03-12)

## v1.0.4 (2024-03-12)

## v1.0.3 (2024-03-12)

### 🐛🚑️ Fixes

- **pypi**: making project logo URL relative

## v1.0.2 (2024-03-12)

### 🐛🚑️ Fixes

- **pypi**: changed project logo URL to `.md`
- **pypi**: updating image URL

## v1.0.1 (2024-03-12)

## v1.0.0 (2024-03-12)

### 💥 Boom

- **pypi**: `MAJOR` version bump to escape file name duplication in PYPI >>> ⏰ 1h 30m

### 🐛🚑️ Fixes

- **pypi**: linking project logo image to `github.com/user/repo/raw/branch/`

## v0.3.0 (2024-03-12)

### ✨ Features

- **break**: breaking change

## v0.2.0 (2024-03-12)

### ✨ Features

- **mandelbrot_channel**: finalized `historical` calculation
- **mandelbrot_channel**: added `calc_mandelbrot_channel_historical`

## v0.1.6 (2024-03-12)

### 🐛🚑️ Fixes

- **docs**: added codefence (testing publish)

## v0.1.5 (2024-03-12)

### 🐛🚑️ Fixes

- **docs**: removed whitespace (testing publish)

## v0.1.4 (2024-03-11)

### ⚡️ Performance

- **price_range**: 35% speed increase, reducing jargon and simplifying transformatio
- **_check_required_cols**: removed redundant `LazyFrame` collect

### ✅🤡🧪 Tests

- **mandelbrot_channel**: finished `price_range()` tests || finished with testing helpers✅
- **setting up test for  prior to refactor**: scope
- **price-range**: error condition test, passing `_rs_method` that doesnt exist
- **vol_filter**: tests filtering ability by counting the rows that are filtered
- **vol_buckets**: added error condition test when columns missig

### 📌➕⬇️ ➖⬆️  Dependencies

- **dev**: added `line_profiler`

## v0.1.3 (2024-03-08)

### 🐛🚑️ Fixes

- **vol_filter**: added column checks

### ⚡️ Performance

- **vol_buckets**: using `_boundary_group_down` to use alternative vol function

### ✅🤡🧪 Tests

- **vol_buckets**: parametrized tet to show difference in boundary grouping logic

## v0.1.2 (2024-03-07)

### ci

- **deps**: bump actions/checkout from 3 to 4
- **deps**: bump actions/checkout from 3 to 4

### ✅🤡🧪 Tests

- **gh-action**: remove `cli` module -- only commented out
- **gh-action**: remove typer test
- **gh-action**: remove unknown argument
- **gh-action**: trying new test.yml file
- **humbldata**: moved `tests` from `jjfantini/humbldata` to `humblFINANCE`

## v0.1.1 (2024-03-07)

### ci

- **deps**: bump actions/setup-python from 4 to 5
- **deps**: bump actions/setup-python from 4 to 5

## v0.1.0 (2024-03-07)

### ✨ Features

- **init**: first commit!

### 🐛🚑️ Fixes

- **prproject.toml**: changed bump_map/_pattern
- **gh-action**: added extra requirements to `bump.yml`
