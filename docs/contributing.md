---
icon: material/account-group-outline
---


# 📝 __Contributing Guidelines__

## 🎯 __Expectations for Contributors__

Here is a set of guidelines that you should follow:

1. Use Cases:
    - Ensure that your contributions directly enhance the humbldata's functionality or extension ecosystem.

2. Documentation:
    - All code contributions should come with relevant documentation, including the purpose of the contribution, how it works, and any changes it makes to existing functionalities.
    - Update any existing documentation if your contribution alters the behavior of the humbldata.

3. Code Quality:
    - Your code should adhere strictly to the humbldata's coding standards and conventions.
    - Ensure clarity, maintainability, and proper organization in your code.

4. Testing:
    - All contributions must be thoroughly tested to avoid introducing bugs to the humbldata.
    - Contributions should include relevant automated tests (unit and integration), and any new feature should come with its test cases.

5. Performance:
    - Your contributions should be optimized for performance and should not degrade the overall efficiency of the humbldata.
    - Address any potential bottlenecks and ensure scalability.

6. Collaboration:
    - Engage actively with the humbldata development team to ensure that your contributions align with the platform's roadmap and standards.
    - Welcome feedback and be open to making revisions based on reviews and suggestions from the community.

## 🏆 __Best Practices__

- Review Platform Dependencies: Before adding any dependency, ensure it aligns with the Platform's existing dependencies.
- Use Loose Versioning: If possible, specify a range to maintain compatibility. E.g., `>=1.4,<1.5`.
- Testing: Test your extension with the Platform's core to avoid conflicts. Both unit and integration tests are recommended.
- Document Dependencies: Use `pyproject.toml` and `poetry.lock` for clear, up-to-date records

## 🐍 __Code Standards__
### 🪺PEP Guidelines
You must adhere to the strict guidelines of coding best practices. Here is a non-exhaustive list of the most important guidelines to follow:

1. **PEP 8**: This is the de-facto code style guide for Python. It is a set of conventions for how to format your Python code to maximize its readability.
    - It is a set of conventions for how to format your Python code to maximize its readability.
2. **PEP 484**: This PEP introduces a standard for type annotations in Python. It aims to provide a standard syntax for type annotations, opening up Python code to easier static analysis and refactoring.
    - It aims to provide a standard syntax for type annotations, opening up Python code to easier static analysis and refactoring.
3. **PEP 621**: This PEP introduces a mechanism to specify project metadata in a standardized way. It aims to provide a standard way to specify project metadata, making it easier for tools to work with Python projects.
    - It aims to provide a standard way to specify project metadata, making it easier for tools to work with Python projects.
4. **PEP 20**: This PEP is a set of aphorisms that capture the guiding principles of Python's design. It is a must-read for any Python developer.
    - It is a set of aphorisms that capture the guiding principles of Python's design. It is a must-read for any Python developer.
??? abstract "The Zen of Python"
      Beautiful is better than ugly.

      Explicit is better than implicit.

      Simple is better than complex.

      Complex is better than complicated.

      Flat is better than nested.

      Sparse is better than dense.

      Readability counts.

      Special cases aren't special enough to break the rules.

      Although practicality beats purity.

      Errors should never pass silently.

      Unless explicitly silenced.

      In the face of ambiguity, refuse the temptation to guess.

      There should be one-- and preferably only one --obvious way to do it.

      Although that way may not be obvious at first unless you're Dutch.

      Now is better than never.

      Although never is often better than *right* now.

      If the implementation is hard to explain, it's a bad idea.

      If the implementation is easy to explain, it may be a good idea.

      Namespaces are one honking great idea -- let's do more of those!

## ➕ Adding a Function

If you want to add a function, first you must decide. What is the context, category and command? Once, you have done that you will need to do these 3 things:

1. **Define `QueryParams` and `Data` Standard Model.**

    Put your new standard model in:

     ```
     humbldata.core.standard_models.<context>.<category>.<your_func>
     ```

    This should be a `.py` file.
    ```
    ~\humbldata\src\humbldata\core\standard_models\<context>\<category>\<command>.py
    ```
    You will then define two classes.
    The `QueryParams` and the `Data`, the fields used to query the data and then the returned data fields, respectively.
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





## 🙏 __Acknowledgment__
   - We acknowledge and thank the OpenBB team for creating such well documented [Guidelines](https://github.com/OpenBB-finance/OpenBBTerminal/blob/develop/openbb_platform/CONTRIBUTING.md#contributor-guidelines).
