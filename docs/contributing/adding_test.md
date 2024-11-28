---
icon: material/file-restore
---

## 🧪 Adding a Test

### Test Requirements
It is required to add tests to cover all the code that you add to the package. Here are the
guidelines to help you organize the tests you need to add.

#### Overview
Tests are categorized into two main types:
1. **Unit Tests**:
   - These test individual units of functionality.
   - They should be independent from other tests and external dependencies.
2. **Integration Tests**:
   - These test the combination of units working together.
   - They verify full functionality and interaction between components.

#### Test Organization
The tests should be organized according to the CCCC framework: Core, Context, Category, Command. The directory structure for tests should reflect this organization.

#### Directory Structure

```
tests/
├── integration/
│   ├── context/
│   │   ├── category/
│   │   │   ├── command/
│   │   │   │   └── test_queryParams_data_fetcher.py
│   │   │   │   └── test_view.py
│   │   │   │   └── test_model.py
│   │   ├── test_methods.py
│   └── test_queryParams.py
└── unittests/
    ├── context/
    │   ├── category/
    │   │   ├── command/
    │   │   │   └── test_helpers.py
    │   │   │   └── test_view.py
    │   │   │   └── test_model.py
    │   │   ├── test_methods.py
    ├── test_helpers.py
```

## 📝 Detailed List of All Tests
### Integration Tests
- **Context: Toolbox**
    - `test_queryParams.py` - test the `standard_models`
- **Category: Technical**
    - `test_methods.py` - test the methods in the class, and ensure they pass the parameters and instantiate the class correctly
- **Command: mandelbrot_channel**
    - `test_queryParams_data_fetcher.py` - test the `fetcher` gets the data correctly and verify it with the standard_models. i.e `MandelbrotData()`
    - `test_view.py` - test the charting visualization creates the right charts
    - `test_model.py` - test logic of functions, uses live data to ensure function runs properly
### Unit Tests
- **Context: Toolbox**
    - `test_helpers.py` - test the `helpers` statically
- **Category: Technical**
    - `test_methods.py` (mock) - test the `methods` but mock the classes so that there are no dependencies on classes actually instantiating themselves.
- **Command: mandelbrot_channel**
    - `test_helpers.py` - test the `helpers` statically
    - `test_view.py` - test the charting visualization returns the correct objects
    - `test_model.py` - test the logic of functions and input validation

!!! tip Use `__init__.py` files to group tests together.

You should use `__init__.py` files to group tests together and provide the correct namespace for `pytest` to find each of the tests, because I have chosen a design pattern to name multiple tests with the same name, and they are just nested in their respective directory.

!!! example Check `/tests` for examples

Take a look at tests that have already been created to get a sense of how to test your classes and functions.

!!! warning When you update Polars version, you need to update the `humblobject` pickle files as serialization is not always backwards compatible.

### Expectations for Test Creation
- **Independence**: Ensure unit tests do not rely on external systems or other tests.
- **Comprehensiveness**: Write tests to cover all possible edge cases.
- **Clarity**: Name tests clearly to indicate what functionality they cover.
- **Consistency**: Follow the CCCC framework for organizing tests.
- **Documentation**: Document any non-trivial logic within the tests for future reference.


