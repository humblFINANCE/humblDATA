## OpenBB Function Usage Summary

This document outlines the files and specific OpenBB (`obb`) functions that need to be refactored to use the new external OpenBB API.

- [ ] **`src/humbldata/portfolio/analytics/watchlist/helpers.py`**
    - [ ] `obb.etf.info`
- [ ] **`src/humbldata/core/utils/openbb_helpers.py`**
    - [ ] `obb.account.login`
    - [ ] `obb.account.save` (currently commented out)
    - [ ] `obb.equity.price.quote`
    - [ ] `obb.equity.profile`
    - [ ] `obb.etf.info`
- [ ] **`src/humbldata/core/standard_models/toolbox/fundamental/humbl_compass_backtest.py`**
    - [ ] `obb.equity.price.historical`
- [ ] **`src/humbldata/core/standard_models/toolbox/fundamental/humbl_compass.py`**
    - [ ] `obb.economy.composite_leading_indicator`
    - [ ] `obb.economy.cpi`
- [...] **`src/humbldata/core/standard_models/toolbox/technical/realized_volatility.py`**
    - [...] `obb.equity.price.historical`
- [x] **`src/humbldata/core/standard_models/toolbox/technical/humbl_momentum.py`**
    - [x] `obb.equity.price.historical`
- [x] **`src/humbldata/core/standard_models/toolbox/technical/humbl_channel.py`**
    - [x] `obb.equity.price.historical`
