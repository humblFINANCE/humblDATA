## v1.23.0 (2025-05-31)

### ✨ Features

- **technical**: add humbl_signal method to Technical controller for signal calculations

### 📌➕⬇️➖⬆️ Dependencies

- **uv**: added test packages

## v1.22.1 (2025-05-22)

### 🐛🚑️ Fixes

- **bump**: added pandas as a dep

## v1.22.0 (2025-05-22)

### ✨ Features

- **bump**: trigger bump

### 📌➕⬇️➖⬆️ Dependencies

- **uv**: added numpy

## v1.21.3 (2025-05-22)

### 🐛🚑️ Fixes

- **openbb_api_client**: implement shared aiohttp ClientSession for improved connection pooling and timeout handling

## v1.21.2 (2025-05-22)

### 🐛🚑️ Fixes

- **watchlist**: refactor humbl_channel fetching and enhance data serialization

## v1.21.1 (2025-05-22)

### 🐛🚑️ Fixes

- **rate_limiter**: enhance logging output and update rate limit usage reporting

## v1.21.0 (2025-05-21)

### ✨ Features

- **env**: add REDIS_URL property to Env class for improved configuration
- **QueryParams**: added EconomyQueryParams models
- **humbl_channel**: OpenBBAPICLient class is working

### 🐛🚑️ Fixes

- **humbl_compass**: reset execution counts and enhance logging output in example notebook
- **humbl_compass**: improve logging for cache hits with Redis location and update example notebook execution counts
- **core_helpers**: using write_ipc vs sink_ipc for safer serialization
- **humblobject**: using Arrows IPC serialization vs built in polars serialization
- **network_helpers**: join a list of strings into a joined string
- **humbl_compass**: move imports to top level
- **humbl_compass**: reset execution counts and improve logging output in example notebook
- **humbl_compass**: enhance logging for cache hits
- **openbb_api_client**: appended rate limited warnings to humblobject response
- **humbl_channel, humbl_momentum**: update OpenBBAPIClien usage in notebooks and mark functions as completed in replaceFunctions.md
- **humblCHANNEL_example**: handle ImportError for 'obb' and clean notebook output

### ♻️ Refactorings

- **humbl_compass**: refactor fetch_data to async in notebooks and backtest logic
- **humbl_compass**: streamline cache key building and remove unused cache logic
- **humbl_compass**: using async caching logic now to prep for openbbapi refactor
- **rules**: update rules for adding QueryParams and refactor to async API client
- **humbl_momentum**: refactor data extraction to use OpenBB API client and async methods
- **openbbapi**: added Price to standard model

### ⚡️ Performance

- **openbba_api_client**: use collect_schema vs schema

## v1.20.22 (2025-05-14)

### 🐛🚑️ Fixes

- **docs**: rmeove unneeded flag

### 📌➕⬇️➖⬆️ Dependencies

- **dep**: added prerelease

## v1.20.21 (2025-05-14)

## v1.20.20 (2025-05-14)

### 🐛🚑️ Fixes

- **docs**: replaced uv pip sync with uv sync

## v1.20.19 (2025-05-14)

### 🐛🚑️ Fixes

- **notebooks**: update execution counts and ID in testing.ipynb

### ♻️ Refactorings

- replace codebase with working files from humblDATA2

## v1.20.18 (2025-05-12)

### 🐛🚑️ Fixes

- **deps**: update redis-cache to python-redis-cache and adjust Python version requirements

## v1.20.17 (2025-05-09)

### 🐛🚑️ Fixes

- **python**: adding python 3.11

## v1.20.16 (2025-05-09)

### 🐛🚑️ Fixes

- **python**: widened the python reqs

## v1.20.15 (2025-05-09)

### 🐛🚑️ Fixes

- **docs**: remove extraneous letter

### 📌➕⬇️➖⬆️ Dependencies

- **add**: redis-cache

## v1.20.14 (2025-05-09)

### 🐛🚑️ Fixes

- **publish**: testing using poetry token

## v1.20.13 (2025-05-09)

### 🐛🚑️ Fixes

- **publish**: no env name, last for the night

## v1.20.12 (2025-05-09)

### 🐛🚑️ Fixes

- **publish**: no token needed

## v1.20.11 (2025-05-09)

### 🐛🚑️ Fixes

- **publish**: testing diff file for python

## v1.20.10 (2025-05-09)

### 🐛🚑️ Fixes

- **version**: bump version to trigger publish

## v1.20.9 (2025-05-09)

### 🐛🚑️ Fixes

- **duplicate**: removed extra description field in pyproject.toml
- **version**: duplicate version
- **version**: wrong version
- **openbb**: fixed yfinance bug by removing lumibot and switching to uv

### ♻️ Refactorings

- **GHA**: changed docs and publish logic to use uv as well

## v1.20.8 (2025-04-30)

### 🐛🚑️ Fixes

- refine humblCOMPASS backtest example and enhance query parameters

## v1.20.7 (2025-04-30)

### 🐛🚑️ Fixes

- update humblCOMPASS backtest example and data model

## v1.20.6 (2025-04-30)

### 🐛🚑️ Fixes

- update notebook examples and backtest logic

## v1.20.5 (2025-04-29)

### ♻️ Refactorings

- **rename**: user_table --> watchlist_table

## v1.20.4 (2025-04-29)

### 🐛🚑️ Fixes

- update humblCHANNEL and humblCOMPASS examples for accuracy

## v1.20.3 (2025-04-17)

### 🐛🚑️ Fixes

- update humblCHANNEL example and data handling

## v1.20.2 (2025-04-17)

### 🐛🚑️ Fixes

- update humblPORTFOLIO example and descriptions

## v1.20.1 (2025-04-16)

### 🐛🚑️ Fixes

- enhance humbl channel examples and data handling

## v1.20.0 (2025-04-16)

### ✨ Features

- update humbl_channel functionality and data handling

## v1.19.2 (2025-04-16)

### 🐛🚑️ Fixes

- enhance humbl_channel data handling

## v1.19.1 (2025-04-15)

### ♻️ Refactorings

- **mandelbrot_channel**: clean up imports and remove unused momentum module

## v1.19.0 (2025-04-15)

### ✨ Features

- **humbl_compass**: update momentum example notebook and enhance plotting logic
- **humbl_compass**: update momentum analysis in example notebook and enhance model definitions
- **humbl_compass**: modularize backtest analysis with enhanced model functions
- **humbl_compass**: add advanced drawdown and recovery metrics to backtest analysis
- **humbl_compass**: expand backtest analysis with investment growth metrics
- **humbl_compass**: enhance backtest with chart generation and regime details

### 🐛🚑️ Fixes

- **humbl_compass**: correct execution counts and output in momentum example notebook

### ♻️ Refactorings

- **humbl_compass**: optimize investment growth calculation and regime processing

## v1.18.2 (2025-02-25)

### 🐛🚑️ Fixes

- **griffe**: remove as dep...need to fix

## v1.18.1 (2025-02-25)

### 🐛🚑️ Fixes

- **docs**: added poetry lock

## v1.18.0 (2025-02-25)

### ✨ Features

- **dependencies**: add griffe for enhanced documentation generation

## v1.17.0 (2025-02-25)

### ✨ Features

- **openbb_helpers**: enhance ETF category retrieval with robust symbol validation
- **constants**: add comprehensive US ETF symbol collections

### ♻️ Refactorings

- **constants**: optimize US ETF symbol list formatting

## v1.16.0 (2025-02-25)

### ✨ Features

- **json**: enhance JSON serialization and decoding for HumblObject

## v1.15.1 (2025-02-24)

### 🐛🚑️ Fixes

- **warnings**: prevent duplicate warnings and improve warning messages

## v1.15.0 (2025-02-24)

### ✨ Features

- **warnings**: enhance warning collection and handling mechanism

## v1.14.0 (2025-02-10)

### ✨ Features

- **humbl_compass**: added .backtest() method
- **logger**: enable isatty option in logger setup for improved output formatting
- **logger**: enable isatty option in logger setup for improved output formatting
- **strategy**: add HumblChannelSingleLong trading strategy

### 🐛🚑️ Fixes

- removed uneeded imports
- **lumibot**: installing lumibot from git branch that still uses pip

## v1.13.0 (2024-12-09)

### ✨ Features

- **momentum**: add simple plot functionality and enhance plot generation
- **momentum**: enhance momentum plotting functionality and add template support

### 🐛🚑️ Fixes

- **test_model**: add comments for clarity on testing structure
- **momentum**: refactor momentum parameters and enhance calculation logic
- **momentum**: refactor momentum calculation to use kwargs and enhance data handling
- **momentum**: enhance momentum calculation and add charting option
- **mandelbrot_channel**: serialize equity historical data and include in HumblObject
- **mandelbrot_channel**: update window_format method to raise TypeError
- **add_command**: refactor method parameters to use **kwargs for improved flexibility
- **mandelbrot_channel**: removed kwargs, using command_params
- **mandelbrot_channel**: update warning logic in Fetcher
- **humbl_compass**: added debug logging

### ♻️ Refactorings

- **notebooks**: organized notebooks

### ✅🤡🧪 Tests

- **momentum**: add integration tests for momentum calculations
- **momentum**: add unit tests for momentum calculations
- **momentum**: add momentum command parameters fixture and integration test

## v1.12.6 (2024-12-03)

### 🐛🚑️ Fixes

- **humbl_compass**: update regime descriptions and key risks for clarity

## v1.12.5 (2024-12-03)

### 🐛🚑️ Fixes

- **openbb_helpers**: enhance get_latest_price function with logging and error handling
- **realized_volatility_helpers**: refactor squared returns calculation for symbol grouping
- **realized_volatility_helpers**: refactor Yang-Zhang volatility calculation for symbol grouping

## v1.12.4 (2024-12-03)

### 🐛🚑️ Fixes

- **realized_volatility_helpers**: refactor Rogers-Satchell volatility calculation for symbol grouping
- **realized_volatility_helpers**: refactor Hodges-Tompkins volatility calculation for symbol grouping
- **realized_volatility_helpers**: refactor Garman-Klass volatility calculation for symbol grouping
- **realized_volatility_helpers**: refactor Parkinson's volatility calculation for symbol grouping
- **mandelbrot_channel**: remove unnecessary transformation of recent_price column

## v1.12.3 (2024-12-03)

### 🐛🚑️ Fixes

- **log_returns**: enhance log return calculation to support grouping by symbol
- **std**: adding .over() logic to calc over symbols
- **calc_realized_volatility**: added more informative warning
- **humblCHANNEL**: view column renamed to recent_price

## v1.12.2 (2024-12-02)

### 🐛🚑️ Fixes

- **humbl_compass**: extended chart shading to 25 for large swings in economies

### 📌➕⬇️➖⬆️ Dependencies

- **dev**: added orjson

## v1.12.1 (2024-12-02)

### 🐛🚑️ Fixes

- **HumblCompassData**: made z-score columns nullable

## v1.12.0 (2024-12-01)

### ✨ Features

- **humbl_compass**: added CLI/CPI Z-Score to the hover template

## v1.11.6 (2024-12-01)

### 🐛🚑️ Fixes

- **humbl_compass**: added warning and set minimum z_score to 3 months

## v1.11.5 (2024-12-01)

### 🐛🚑️ Fixes

- **humbl_compass**: change delta calculation to work with quarterly and monthly data

## v1.11.4 (2024-11-30)

### 🐛🚑️ Fixes

- **mandelbrot_channel**: removed adjustments parameter
- **notebooks, src**: enhance humblCHANNEL and humblCOMPASS functionality
- **tests**: changed column name in a view test

## v1.11.3 (2024-11-30)

### 🐛🚑️ Fixes

- **rename**: renamed IPYNB and bumping for openbb req

## v1.11.2 (2024-11-30)

### 🐛🚑️ Fixes

- **humbl_compass**: changed to inner join

## v1.11.1 (2024-11-29)

### 🐛🚑️ Fixes

- **humbl_compass**: add empty extra field if it doenst exist

## v1.11.0 (2024-11-29)

### ✨ Features

- **humbl_compass**: added humbl_regime recommendations

## v1.10.1 (2024-11-28)

### 🐛🚑️ Fixes

- **toolbox**: symbols param can now be nullable

### 📌➕⬇️➖⬆️ Dependencies

- **update**: security updates

## v1.10.0 (2024-11-28)

### ✨ Features

- **humbl_compass**: added humbl_regime column
- **user_table**: normalize U/D Ratio to 0-1

### 🐛🚑️ Fixes

- **humblobject**: reserialized object with neew polars version
- **user_table**: updated values to match using new normalized ratio
- **humbl_compass**: mor informative categroy
- **humbl_compass**: merge warnings form context and fetcher
- **toolbox**: added warning message variable --> DRY
- **toolbox**: removed .lower() to match the membership tiers

### 📌➕⬇️➖⬆️ Dependencies

- **update**: polars

## v1.9.4 (2024-11-14)

### ♻️ Refactorings

- **rename**: renmed power to humblPOWER

## v1.9.3 (2024-11-14)

### ♻️ Refactorings

- **rename**: updated membership names to prefix with humbl

### ⚡️ Performance

- **humblCOMPASS:view**: rewrite dicts as literals

## v1.9.2 (2024-10-17)

### 🐛🚑️ Fixes

- **humblCOMPASS**: added humblREGIME annotations
- **humblCOMPASS**: shading quadrants and showing data with a buffer

## v1.9.1 (2024-10-14)

### 🐛🚑️ Fixes

- **humblCOMPASS**: serialize the transformed_data

## v1.9.0 (2024-10-14)

### ✨ Features

- **humblCOMPASS**: v1 of humblCOMPASS finished
- **command**: new humbl_compass command in fundamental category

### 🐛🚑️ Fixes

- **humblCOMPASS**: cannot calculate z-score if you are a peon member
- **imports**: removed unused imports and organized
- **commitizen**: added small keyboard commit shortcut
- **poe: add_command**: added new logging and warnings to the standard_model
- **poe: add_command**: fixed logic to not overwrite files and updates content instead

## v1.8.1 (2024-07-25)

### 🐛🚑️ Fixes

- **create_historical_plot**: rename column name

### ✅🤡🧪 Tests

- **humblobject**: remove test assertions;

### 📌➕⬇️ ➖⬆️  Dependencies

- **poetry**: update

## v1.8.0 (2024-07-23)

### ✨ Features

- **mandelbrot_chanel**: using a  instead of
- **uvloop**: now using uvloop execution

## v1.7.1 (2024-07-19)

### 🐛🚑️ Fixes

- **pandera**: move to  to remove column names error

## v1.7.0 (2024-07-19)

### ✨ Features

- **Toolbox**: replace  w/
- **warnings**: piping warnings from ToolboxQueryParams into HumblObject

### ✅🤡🧪 Tests

- **remove**: (-) as validation is internal
- **ToolboxQueryParams**: testing start_date_validator and date return type
- **humblobjject**: added  to make sure JSON chart data is valid

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
