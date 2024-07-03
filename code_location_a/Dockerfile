ARG PYTHON_IMAGE_VERSION=3.11.6-slim

FROM python:$PYTHON_IMAGE_VERSION AS installer

RUN apt update && apt -y install curl

ENV POETRY_HOME=/app/poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.7.1 python3 -

WORKDIR /app

COPY poetry.lock poetry.toml pyproject.toml ./

RUN /app/poetry/bin/poetry install --no-root

FROM python:$PYTHON_IMAGE_VERSION

WORKDIR /app

COPY --from=installer /app/.venv ./.venv

COPY definitions ./definitions

#RUN addgroup --system --gid 1001 dagster
#RUN adduser --system --uid 1001 dagster
#RUN chown -R dagster:dagster /app
#USER dagster

ENV DAGSTER_HOME=/app/
ENV PYTHONPATH=/app/
ENV PATH="/app/.venv/bin:${PATH}"
