FROM python:3.12.13-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BENCHMARK_OUTPUT=/app/benchmarks/results/summary.json

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir ".[dev]" \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/benchmarks/results \
    && chown -R appuser:appuser /app

COPY tests ./tests
COPY benchmarks ./benchmarks
COPY project.yaml ./

USER appuser

ENTRYPOINT ["feature-store-lite"]
CMD ["benchmark"]
