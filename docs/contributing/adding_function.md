## ➕ Adding a Function

If you want to add a function, first you must decide. What is the context, category and command? Once, you have done that you will need to do these 3 things:

1. ### **Define `QueryParams` and `Data` Standard Model.**

    Put your new standard model in:

     ```
     humbldata.core.standard_models.<context>.<category>.<your_func>
     ```

    This should be a `.py` file.
    ```
    ~\humbldata\src\humbldata\core\standard_models\<context>\<category>\<command>.py
    ```

    You will then define two classes: `QueryParams` and `Data`. The fields used to query the data and then the returned data fields, respectively.

    ```py
    """
    <Your Function> Standard Model.

    Context: Toolbox || Category: Technical || Command: <Your Function>.

    This module is used to define the QueryParams and Data model for the
    <Your Function> command.
    """
    from humbldata.core.standard_models.abstract.data import Data
    from humbldata.core.standard_models.abstract.query_params import QueryParams
    class <YourFunc>QueryParams(QueryParams):
        """
        QueryParam for the <Your Function> command.
        """
    class <YourFunc>Data(Data):
        """
        Data model for the <Your Function> command.
        """
    ```
2. ### **Add the Function Logic (model.py) to the `Context` module**

    Each `<command>` has a `model.py`, `view.py` and `helper.py` file.

    Add these files to the `Context` module.
    ```py
    humbldata/
    ├── <context>/
    │   ├── <category>/
    │   │   ├── <your_func>/
    │   │   │   ├── model.py
    │   │   │   ├── view.py
    │   │   │   └── helper.py

    humbldata.<context>.<category>.<your_func>.model/view/helper.py

    # i.e

    humbldata/
    ├── toolbox/
    │   ├── technical/
    │   │   ├── mandelbrot_channel/
    │   │   │   ├── model.py
    │   │   │   ├── view.py
    │   │   │   └── helper.py

    humbldata.toolbox.technical.mandelbrot_channel.model
    ```

     !!! tip

     It is common practice in the repo to prepend your logic function, in the `model.py` file, with `calc_...`.
     So the function would be `calc_mandelbrot_channel`.
