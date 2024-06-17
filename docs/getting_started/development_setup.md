---
icon: material/crane
---


# 🏗️ Development Setup

Here, you will find all the settings needed to setup your machine to contribute to the project, and also understand the coding practices that went into making this package, so you can follow along and understand the code structure.

## Environment Setup
You can add a `.env` file to the root of the project to set environment variables. This is useful if you want to use your own Personal Access Token via OpenBB for your own data vendor support. Just set the `OBB_PAT` variable to your own key.

??? tip "Useful Developer Commands"
    - `micromamba activate -p ./menv`: activate the micromamba env
    - `poe`: list all the available commands for the package
    - `poetry add {package}`: install a run time dependency and add it to `pyproject.toml` and `poetry.lock`. Add `--group test` or `--group dev` to install a test or development dependency, respectively.
    - `poetry update`: upgrade all dependencies to the latest versions allowed by `pyproject.toml`.
    - `cz bump`: bump the package's version, update the `CHANGELOG.md`, and create a git tag, settings can be made in both `cz-config.js` and `bumpversion.yml`.
    - `cruft update`: update the current project to mirror the latest cookiecutter template
    - `mkdocs serve`: start a server for documentation


## 🎣 Hooks

This project uses two hooks, `pre_gen_project.py` and `post_gen_project.py`, which are scripts that run before and after the project generation process, respectively. `post_gen_project.py` is repsonsible for setting up the micromamba environment.


## 🍪 Cruft

This project uses cruft to manage the template and update the project with the latest changes.
This has one caveat for now. While using commitizen and customizing the commit messages in `pyproject.toml` the `cruft update` command will not work as expected. I think because emojis in the `pyproject.toml` are not read with the correct encoding.

??? example "Solution"
    If you need to perform a `cruft update`, please just remove the sections with emojis, and run `cruft update`. Then, you will be able to insert the emojis defined in the `[tool.commitizen.customize]` from the original template, after the update has completed.

    I should look to move to just use `czg` or `cz-git` instead of `commitizen` + `cz-customizable` + `cz-conventional-gitmoji`.

    ??? abstract "Manually Upload `pyproject.toml` content"
        If you need to manually add the emojis to the `pyproject.toml` file, you can use the following code to add the emojis to the `pyproject.toml` file.

        ```python
        [tool.commitizen]
        name = "cz_gitmoji"
        version = "0.11.4"
        tag_format = "v$version"
        update_changelog_on_bump = true
        annotated_tag = true
        bump_message = "🔖 bump(release): v$current_version → v$new_version"
        version_files = ["pyproject.toml:^version"]
        path = ".cz-config.js"

        [tool.commitizen.customize]
        example = "feat: this feature enables customizing through pyproject.toml file"
        schema = """
        <type>(<scope>): <subject> \n
        <BLANK LINE> \n
        <body> \n
        <BLANK LINE> \n
        (BREAKING CHANGE: )<breaking> \n
        <BLANK LINE> \n
        (ISSUES: )<footer>
        """
        schema_pattern = "(?s)(✨ feat|🐛 fix|🚑 hotfix|🔧 chore|♻️ refactor|🚧 WIP|📚 docs|⚡️ perf|💄 style|🏗️ build|👷 ci|✅ test|⏪ revert|➕ add_dep|➖ rem_dep)(\\(\\S+\\))?!?:( [^\\n\\r]+)((\\n\\n.*)|(\\s*))?$"
        bump_pattern = "^(✨ feat|🐛 fix|🚑 hotfix|⚡️ perf|♻️ refactor|⏪ revert|➕ dep-add|➖ dep-rm)"
        bump_map = {"BREAKING CHANGE" = "MAJOR", "✨ feat" = "MINOR", "🐛 fix" = "PATCH", "🚑 hotfix" = "PATCH", "⚡️ perf" = "PATCH", "♻️ refactor" = "PATCH"}
        change_type_order = ["BREAKING CHANGE", "✨ feat", "🐛 fix", "🚑 hotfix", "♻️ refactor", "⚡️ perf", "🏗️ build", "💄 style", "📚 docs", "➕ dep-add", "➖ dep-rm"]
        info_path = "cz_customize_info.txt"
        info = """
        This is customized commitizen info
        """
        commit_parser = "^(?P<change_type>✨ feat|🐛 fix|🚑 hotfix|🔧 chore|♻️ refactor|🚧 WIP|📚 docs|⚡️ perf|💄 style|🏗️ build|👷 ci|✅ test|⏪ revert|➕ dep-add|➖ dep-rm):\\s(?P<message>.*)?"
        changelog_pattern = "^(✨ feat|🐛 fix|🚑 hotfix|🔧 chore|♻️ refactor|🚧 WIP|📚 docs|⚡️ perf|💄 style|🏗️ build|👷 ci|✅ test|⏪ revert|➕ dep-add|➖ dep-rm)?(!)?"
        change_type_map = {"🏗️ build" = "Build", "👷 ci" = "CI", "📚 docs" = "Docs", "✨ feat" = "Feat", "🐛 fix" = "Fix", "🚑 hotfix" = "Hotfix", "⚡️ perf" = "Perf", "♻️ refactor" = "Refactor", "💄 style" = "Style", "✅ test" = "Test", "🔧 chore" = "Chore", "⏪ revert" = "Revert", "➕ dep-add" = "Added Dependency", "➖ dep-rm" = "Removed Dependency"}
        ```


## 🐭 Setup Micromamba Environment with Poetry

This section shows users how to setup your environment using your `micromamba` file and `poetry`.
This project uses a micromamba environment. The micromamba environment will be automatically setup for you after generating the project from the template using a `post_gen_project` hook. The following steps are for reference only (if you need to recreate the environment). This assumes you use `bash` as your shell.

??? warning "Prerequisites"
    1. Installing [micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html#operating-system-package-managers)

    ```bash
    # Windows (Powershell)
    Invoke-Expression ((Invoke-WebRequest -Uri https://micro.mamba.pm/install.ps1).Content)
    ```

    ```bash
    # Linux and macOS
    "${SHELL}" <(curl -L micro.mamba.pm/install.sh)
    ```

??? info "Creating Micromamba Environment"

    1. I created the environment with a `--prefix` and not a name, to ensure that it installed in my project directory, not the default path. This is executed in the project root dir.

        ```bash
        micromamba env create --file micromamba_env.yml
        ```

    2. To avoid displaying the full path when using this environment, modify the `.condarc` file to show the environment name as the last directory where the environment is located. This can be done manually or by running the command `micromamba config --set env_prompt '({name})'`.

        ```bash
        micromamba config --set env_prompt '({name})'
        ```

        After the modification, your `.condarc` file should look like this:

        ```yaml
        channels:
          - conda-forge
          - defaults
        env_prompt: ({name})
        repodata_threads: 2
        change_ps1: false
        envs_dirs:
          - ~/micromamba/envs
        ```

    3. Activate the environment

        ```bash
        micromamba init bash / micromamba init zsh
        micromamba activate ./menv
        ```

    4. Check if poetry is installed

        ```bash
        poetry --version
        # make sure it is the latest version
        # can use mamba search -f poetry
        ```
    5. If poetry is showing any errors like:

        - `Failed to create process`
        - `No Python at <path>`

        You can simply run:
        ```bash
        micromamba remove -p ./menv poetry
        micromamba install -p ./menv poetry
        ```
    6. If the python version doesnt match, just install the version you would like:

        ```bash
        micromamba install -p ./menv python=3.12.1
        ```

    6. Install Packages from `poetry.lock` / `pyproject.toml`

        ```bash
        poetry install
        ```

??? info "Setting Up `Commitizen`"
    I am using the [`vscode-commitizen`](https://marketplace.visualstudio.com/items?itemName=KnisterPeter.vscode-commitizen) extension to integrate `commitizen` into my workflow.
    This allows for nice keyboard shortcuts and UI integration. I have also installed `cz_customizable` globally to allow me to customize the commit message template using `cz-config.js`.

    The `pyproject.toml` file has the specifications for `cz_customizable` and `commitizen` to work together.

    Follow the [quickstart guide](https://github.com/leoforfree/cz-customizable?tab=readme-ov-file#quick-start-new-recommended) to setup `cz-customizable`. You need to install
    `cz-customizable` globally in order for the vscode extension to work along with the settings provided in the `pyproject.toml` file. This will allow for custom commit types and user-specific settings.

    You need these two files, to ensure automatic commit linting, and package versioning.

    - [x] `./pre-commit-config.yml`
    - [x] `./github/workflows/bumpversion.yml`

## ⚡ Setup Github Workflows

There are __4__ pre-made github actions that are used with this package. Some actions require API_KEYS/TOKENS to work. Add your tokens to the secrets manager in your repo settings.

??? abstract "1. `bump.yml`"
    This workflow automates the versioning of the project using bumpversion.
    - Tokens/Secrets:
        - `GH_PAT`: Github Personal Access Token
    You need to create a Github Personal Access Token and add it to your secrets manager in your repo settings.

??? abstract "2. `deploy.yml`"
    This workflow is responsible for deploying the project. It is triggered on push events that include tags in the format "v(x.x.x)" and also manually through the GitHub Actions UI.

    The workflow runs on an Ubuntu-latest environment and only if the GitHub reference starts with 'refs/tags/v'.

    - Steps:
        - Checking out the repository.
        - Logging into the Docker registry.
        - Setting the Docker image tag.
        - Building and pushing the Docker image.
    - Tokens/Secrets:
        - `GITHUB_TOKEN`: This is a GitHub secret used for authentication.
        - `DOCKER_REGISTRY`: This is an environment variable set to 'ghcr.io'.
        - `DEFAULT_DEPLOYMENT_ENVIRONMENT`: This is an environment variable set to 'feature'.
        - `POETRY_HTTP_BASIC__USERNAME`: This is a secret used for authentication with the private package repository.
        - `POETRY_HTTP_BASIC__PASSWORD`: This is a secret used for authentication with the private package repository.
??? abstract "3. `publish.yml`"
    This workflow is responsible for publishing the project. It is triggered when a new release is created.

    The workflow runs on an Ubuntu-latest environment.

    - Steps:
        - Checking out the repository.
        - Setting up Python with the specified version.
        - Installing Poetry, a tool for dependency management and packaging in Python.
        - Publishing the package using Poetry. If a private package repository is specified, the package is published there. Otherwise, it is published to PyPi.
    - Tokens/Secrets:
        - `GITHUB_TOKEN`: This is a GitHub secret used for authentication.
        - `POETRY_HTTP_BASIC__USERNAME`: This is a secret used for authentication with the private package repository.
        - `POETRY_HTTP_BASIC__PASSWORD`: This is a secret used for authentication with the private package repository.
        - `POETRY_PYPI_TOKEN_PYPI`: This is a secret used for authentication with PyPi, if the package is being published there.
??? abstract "4. `test.yml`"
    This workflow is responsible for testing the project. It is triggered on push events to the main and master branches, and on pull requests.

    The workflow runs on an Ubuntu-latest environment and uses the specified Python version.

    - Steps:
        - Checking out the repository.
        - Setting up Node.js with the specified version.
        - Installing @devcontainers/cli.
        - Starting the Dev Container.
        - Linting the package.
        - Testing the package.
        - Uploading coverage.
    - Tokens/Secrets:
        - `GITHUB_TOKEN`: This is a GitHub secret used for authentication.