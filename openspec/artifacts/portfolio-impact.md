# Portfolio Impact: feature-store-lite

## Program

- Program id: `mlops-data-platform`
- Program name: MLOps and Data Platform
- Component pack: `mlops-data-platform`

## System Story

Supplies #21 with reproducible, point-in-time correct training features and a local online retrieval contract while #26 protects source quality and #22 observes model behavior.

This repository is not a standalone demo. It is one part of the MLOps and Data Platform system and should produce reusable fixtures, benchmark patterns, and decisions for later repositories.

## Proficiency Signal

- Primary profile: `python`
- Stack profile: `python-ml`
- Stack:
- python-3.12
- feast-0.64.0
- pandas-2.3.3
- pyarrow-25.0.0
- parquet
- sqlite
- docker
- jsonschema-4.26.0

## Post Angle

Open with online_read_latency_p95_ms = 45.65 ms and 1,061.95 entity values/s, then show how #26's validated batch crosses a versioned contract into #23 without source coupling.
