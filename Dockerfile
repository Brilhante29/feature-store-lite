FROM python:3.12.14-slim-trixie@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea AS build

RUN apt-get update && apt-get upgrade --yes && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml constraints.lock LICENSE ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/pip \
    PIP_CONSTRAINT=/build/constraints.lock \
    python -m pip wheel --wheel-dir /wheels ".[dev]"

FROM python:3.12.14-slim-trixie@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

RUN apt-get update && apt-get upgrade --yes && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BENCHMARK_OUTPUT=/app/benchmarks/results/summary.json

WORKDIR /app

COPY constraints.lock LICENSE ./
COPY --from=build /wheels /opt/wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/opt/wheels \
        -c constraints.lock "feature-store-lite[dev]==1.0.0" \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/benchmarks/results \
    && chown -R appuser:appuser /app

COPY tests ./tests
COPY src ./src
COPY benchmarks ./benchmarks
COPY contracts ./contracts
COPY tools/build_v2_evidence.py ./tools/build_v2_evidence.py
COPY tools/aggregate_results.py ./tools/aggregate_results.py
COPY project.yaml ./

USER appuser

ENTRYPOINT ["feature-store-lite"]
CMD ["benchmark"]
