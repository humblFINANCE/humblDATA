## v1.6.5 (2024-07-17)

### 🐛🚑️ Fixes

- **openbb_helpers**: replaces  with

## v1.6.4 (2024-07-16)

### 🐛🚑️ Fixes

- **mandelbrot_channel**: specifying binary serlization for return data
- **serialization**:  now accepts  serialized objs
- **test_data**: updated pickled  with new serialization from polars
- **polars**: replaced  w/
- **pandera/pytest**: ignoring  for pandera validation in pytest
- **user_table**: rounds final data values to 2 decimal places
- **polars**: using  instead of df.columns
- **humblObject**: added serialization format type --> json
- **remove**: remove field from

### 📌➕⬇️ ➖⬆️  Dependencies

- **update**: openbb, polars, pandera, python: lock to newer versions
- **poetry**: ran

## v1.6.3 (2024-07-16)

### 🐛🚑️ Fixes

- **user_table**: using  not

### ✅🤡🧪 Tests

- **passing**:  all tests passing 🙌
- **fix**: removed  from UserTableQP & fixed validator logic
- **fix**: fixed column name erros, and assertion errors
- **fix**: mocking at module level rather than directly mocking the function

## v1.6.2 (2024-07-10)

### 🐛🚑️ Fixes

- **MandelbrotCHannelFetcher**: updated to match You must specify at least one file, pid, or task.
- **user_table_engine**: added  to pass along to the toolbox creation
- **aget_etf_category**: updated docs, and added  prior to column selection
- **Fetcher**: collect LF's before data validation with pandera, return LF
- **aget_sector_filter**: filter etf_data to only include symbols that are in etf_symbols
- **aget_equity_sector**: casting NULL column to string if DF with null values created
- **user-table.helpers**: updated You must specify at least one file, pid, or task.
- **MandelbrotChannelFetcher**: added

### ✅🤡🧪 Tests

- **tesy_queryParams**: updated  QueryParams validators and test
- **user_table**: added  to test live integration
- **user_table.helpers**: adding unittests for all user_table helper functions

### 📌➕⬇️ ➖⬆️  Dependencies

- **dev**: added

## v1.6.1 (2024-07-07)

## v1.6.0 (2024-07-07)

### ✨ Features

- **UserTable**:  available in
- **humblObject**: added  method w/ tests
- **humblobject**: added  method -- not tested yet

### 🐛🚑️ Fixes

- remove extra method

### build

- **deps-dev**: bump ruff from 0.4.9 to 0.5.0
- **deps-dev**: bump tenacity from 8.4.1 to 8.4.2
- **deps-dev**: bump scipy from 1.13.1 to 1.14.0
- **deps-dev**: bump email-validator from 2.1.2 to 2.2.0
- **deps-dev**: bump exchange-calendars from 4.5.4 to 4.5.5

## v1.5.0 (2024-06-30)

### ✨ Features

- **aget_latest_price**: collects  for etf and

### 🐛🚑️ Fixes

- **QueryParams**: removed  for field typing
- **upper_symbol validator**: added pl.Series typing
- **ToolboxQueryParams**: added  type to valid symbols input
- **aget...filter**: renaming columns and nnormalizing category in the filter
- **aget_etf_sector**: asigning result to
- **aget_etf_sector**: now retunrs clean data if it gets an ETF or EQUITY symbol

## v1.4.0 (2024-06-24)

### ✨ Features

- **user_table**: added  &  &
- **poethepoet**: add a function to generate functions for

### 🐛🚑️ Fixes

- **get_latest_price**: 🚨 removed  so now returns a lazyframe
- **content**: using  for models vs  from pydantic
- **imports**: remove
- **clean_name**: fixes name cleaning methods for PascalCase, snake_case, camelCase
- **clean_name**: correclty converts text to
- **poethepoet**:  now generating all files successfully
- **path**: added  directory to path in function

### ✅🤡🧪 Tests

- **unittests**: added a template for a mocked unittest for
- **Category: Technical**: added method testing to ensure correct parameter passing

## v1.3.0 (2024-06-20)

### ✨ Features

- add default selection of
- **standard_models**: added  validation to
- **standard_models**: added date validation to
- **standard_models**: added new validator to  class for  param

### ✅🤡🧪 Tests

- updated all test data, all are passing
- **integration**: fixed test for mandelbrot_channel integration
- **test_data**: renamed and added a parquet file of historical mandelbrot
- **updating**: replacing old test data with newtest data, simpler interface
- **data**: added necessary data for tests to succeed

### 📌➕⬇️ ➖⬆️  Dependencies

- **update**: updated  to solve  error
- **update**: updated

## v1.2.1 (2024-06-17)

### 🐛🚑️ Fixes

- **mandelbrot_channel fetcher**: added  if no chart is requested
- **volatility_helpers**: replaced  w new function

### build

- **deps-dev**: bump more-itertools from 10.2.0 to 10.3.0
- **deps-dev**: bump safety from 3.2.2 to 3.2.3
- **deps-dev**: bump email-validator from 2.1.1 to 2.1.2
- **deps-dev**: bump urllib3 from 2.2.1 to 2.2.2
- **deps-dev**: bump tenacity from 8.3.0 to 8.4.1

### 📌➕⬇️ ➖⬆️  Dependencies

- **update**: poetry update
- **update**: poetry update
- **update**: poetry update
- **update**: polars to 0.20.31
- **update**: `poetry update`
- **update**: update deps

## v1.2.0 (2024-03-22)

### ✨ Features

- **plotly_theme**: `humblDATA` watermark on graph
- **HumblObject**: `.show()` method shows the charts
- **mandelbrot_channel::view**: integrate `chart` into `MandelbrotChannelQueryParams`
- **mandelbrot_channel**: `chart` parameter now in `MandelbrotChannelQueryParams`
- **HumblObject**: added `raw_data` Field for data used in command calculation
- **mandelbrot_channel**: `Fetcher` now returns `HumblObject`
- **core**: initial `HumblObject` class defined
- **core**: added `Chart` object to safely type charts in `Toolbox`

### 🐛🚑️ Fixes

- **mandelbrot_channel::view**: plotting function returns `Chart` object
- **mandelbrot_channel::view**: view logic wokriing with both historical and current data
- **command_params**: custom `@field_validator` to ensure subclass of `QueryParams`

### ✅🤡🧪 Tests

- **HumblObject**: test each method in the object
- **mandelbrot_channel::view**: test for `create_current_plot()`
- **mandelbrot_channel::view**: basic test asserting `Figure` class
- **HumblObject**: basic `command/context_param` & `provider` tests
- **realized_volatility**: adjusted locked answers
- **mandelbrot_channel**: added `to_polars()` to test objects to get the DF for assertions

### 📌➕⬇️ ➖⬆️  Dependencies

- **poetry**: added `pandera` 0.19.0b0 instead of direct dependency from `git`

## v1.1.0 (2024-03-19)

### ✨ Features

- **MandelbrotChannelQueryParams**: `context_params` & `command_params` are being routed correctly

### 🐛🚑️ Fixes

- **MandelbrotChannelFetcher**: if only one symbol is queried, add a symbol column w/ the symbol
- **ToolboxQueryParams**: fixed `@field_validator` to work with list or csv in a str
- **ToolboxQueryParams**: added default date generation

### ✅🤡🧪 Tests

- **mandelbrot_channel**: finsihed integration tests & renamed standard_model file
- **ToolboxQueryPArams**: added test for custm `@field_validator`
- **queryparams & data**: added simple tests to check vpydantic validation is running right
- **mandelbrot_channel_historical**: added successful tests asserting googl, amd and pct values

### 📌➕⬇️ ➖⬆️  Dependencies

- **pandera**: trying github install of initial pandera update for `pl` supprt

## v1.0.17 (2024-03-14)

### 🐛🚑️ Fixes

- **docs.yml**: forcing the gh-deploy command

## v1.0.16 (2024-03-14)

### 🐛🚑️ Fixes

- **mandelbrot_channel**: removed unecessary imports, added `dt` to standard_model

## v1.0.15 (2024-03-14)

### 🐛🚑️ Fixes

- **gh-actions**: `test,yml` skips with bump commit, `docs.yml` uses mkdocs

## v1.0.14 (2024-03-14)

### 🐛🚑️ Fixes

- **bump.yml**: made contains string more specific to bump message
- **bump.yml**: removed `:` from contains string

## v1.0.13 (2024-03-14)

### 🐛🚑️ Fixes

- **bump.yml**: removed random r character

## v1.0.12 (2024-03-14)

### 🐛🚑️ Fixes

- **bump.yml**: replacing `startsWith` w/ `contains` to skip when commit has bump

## v1.0.11 (2024-03-14)

### 🐛🚑️ Fixes

- **bump.yml**: added 🔖 emoji to commit message to skip

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
