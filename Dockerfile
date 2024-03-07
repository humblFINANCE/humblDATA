# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.11.7
FROM python:3.11.7-slim AS base

# Remove docker-clean so we can keep the apt cache in Docker build cache.
RUN rm /etc/apt/apt.conf.d/docker-clean

# Configure Python to print tracebacks on crash [1], and to not buffer stdout and stderr [2].
# [1] https://docs.python.org/3/using/cmdline.html#envvar-PYTHONFAULTHANDLER
# [2] https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user and switch to it [1].
# [1] https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user
ARG UID=1000
ARG GID=$UID
RUN groupadd --gid $GID user && \
    useradd --create-home --gid $GID --uid $UID user --no-log-init && \
    chown user /opt/
USER user

# Install necessary tools
RUN apt-get update && apt-get install -y wget tar bash

# Install micromamba
RUN wget -qO- https://micromamba.snakepit.net/api/micromamba/linux-64/latest | tar -xvj bin/micromamba
# Make micromamba executable
RUN chmod +x bin/micromamba
# Create a new micromamba environment
RUN ./bin/micromamba create -y -n menv python=${PYTHON_VERSION}
# Activate the micromamba environment
RUN echo "source /opt/conda/etc/profile.d/conda.sh && conda activate menv" >> ~/.bashrc

# Set the working directory.
WORKDIR /workspaces/humbldata/



FROM base as poetry

USER root

# Install Poetry in separate micromamba env so it doesn't pollute the main env.
ENV POETRY_VERSION 1.7.1
ENV POETRY_MICROMAMBA_ENV /opt/poetry-env
RUN --mount=type=cache,target=/root/.cache/pip/ \
    ./bin/micromamba create -y -n $POETRY_MICROMAMBA_ENV python=${PYTHON_VERSION} && \
    /bin/bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate $POETRY_MICROMAMBA_ENV && pip install poetry~=$POETRY_VERSION" && \
    ln -s $POETRY_MICROMAMBA_ENV/bin/poetry /usr/local/bin/poetry

# Install compilers that may be required for certain packages or platforms.
RUN --mount=type=cache,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt/ \
    apt-get update && \
    apt-get install --no-install-recommends --yes build-essential

USER user

# Install the run time Python dependencies in the micromamba environment.
COPY --chown=user:user poetry.lock* pyproject.toml /workspaces/humbldata/
RUN mkdir -p /home/user/.cache/pypoetry/ && mkdir -p /home/user/.config/pypoetry/ && \
    mkdir -p src/humbldata/ && touch src/humbldata/__init__.py && touch README.md
RUN --mount=type=cache,uid=$UID,gid=$GID,target=/home/user/.cache/pypoetry/ \
    /bin/bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate menv && poetry install --only main --no-interaction"

# Rest of the Dockerfile remains the same...
# Persist output generated during docker build so that we can restore it in the dev container.
COPY --chown=user:user .pre-commit-config.yaml /workspaces/humbldata/
RUN mkdir -p /opt/build/poetry/ && cp poetry.lock /opt/build/poetry/ && \
    git init && pre-commit install --install-hooks && \
    mkdir -p /opt/build/git/ && cp .git/hooks/commit-msg .git/hooks/pre-commit /opt/build/git/

# Configure the non-root user's shell.
ENV ANTIDOTE_VERSION 1.8.6
RUN git clone --branch v$ANTIDOTE_VERSION --depth=1 https://github.com/mattmc3/antidote.git ~/.antidote/ && \
    echo 'zsh-users/zsh-syntax-highlighting' >> ~/.zsh_plugins.txt && \
    echo 'zsh-users/zsh-autosuggestions' >> ~/.zsh_plugins.txt && \
    echo 'source ~/.antidote/antidote.zsh' >> ~/.zshrc && \
    echo 'antidote load' >> ~/.zshrc && \
    echo 'eval "$(starship init zsh)"' >> ~/.zshrc && \
    echo 'HISTFILE=~/.history/.zsh_history' >> ~/.zshrc && \
    echo 'HISTSIZE=1000' >> ~/.zshrc && \
    echo 'SAVEHIST=1000' >> ~/.zshrc && \
    echo 'setopt share_history' >> ~/.zshrc && \
    echo 'bindkey "^[[A" history-beginning-search-backward' >> ~/.zshrc && \
    echo 'bindkey "^[[B" history-beginning-search-forward' >> ~/.zshrc && \
    mkdir ~/.history/ && \
    zsh -c 'source ~/.zshrc'
