param(
  [string]$Image = "feature-store-lite:benchmark",
  [int]$Entities = 128,
  [int]$BatchSize = 32,
  [int]$Iterations = 300,
  [int]$Warmups = 10,
  [int]$Repetitions = 3,
  [string]$HardwareClass = "local-docker",
  [string]$ResultsDirectory = "",
  [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$results = if ($ResultsDirectory) {
  [IO.Path]::GetFullPath($ResultsDirectory)
} else {
  Join-Path $root "benchmarks/results"
}
$publication = if ($OutputPath) {
  [IO.Path]::GetFullPath($OutputPath)
} else {
  Join-Path $root "benchmarks/publication/feature-store-v2.json"
}

if ($Entities -lt 8) { throw "Entities must be at least 8" }
if ($BatchSize -lt 1 -or $BatchSize -gt $Entities) { throw "BatchSize must be between 1 and Entities" }
if ($Iterations -lt 3) { throw "Iterations must be at least 3" }
if ($Warmups -lt 1) { throw "Warmups must be positive" }
if ($Repetitions -lt 3) { throw "Repetitions must be at least 3" }

$treeState = @(git -C $root status --porcelain --untracked-files=normal)
if ($LASTEXITCODE -ne 0) { throw "Cannot inspect Git tree" }
if ($treeState.Count -ne 0) { throw "Benchmark requires a clean Git tree" }
$sourceCommit = (git -C $root rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $sourceCommit -notmatch '^[0-9a-f]{40}$') {
  throw "Cannot resolve exact source commit"
}

New-Item -ItemType Directory -Force -Path $results | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $publication) | Out-Null
Get-ChildItem -LiteralPath $results -Filter "run-*.json" -File -ErrorAction SilentlyContinue |
  Remove-Item -Force
$summaryPath = Join-Path $results "summary.json"
if (Test-Path -LiteralPath $summaryPath) { Remove-Item -LiteralPath $summaryPath -Force }

docker build -t $Image $root
if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
$imageDigest = (docker image inspect $Image --format '{{.Id}}').Trim()
if ($LASTEXITCODE -ne 0 -or $imageDigest -notmatch '^sha256:[0-9a-f]{64}$') {
  throw "Cannot resolve image digest"
}
$artifactOutput = (docker run --rm --entrypoint sha256sum $Image /opt/wheels/feature_store_lite-1.0.0-py3-none-any.whl).Trim()
if ($LASTEXITCODE -ne 0 -or $artifactOutput -notmatch '^([0-9a-f]{64})\s+') {
  throw "Cannot resolve application wheel digest"
}
$artifactDigest = "sha256:" + $Matches[1]
$isLinuxHost = [bool](Get-Variable IsLinux -ValueOnly -ErrorAction SilentlyContinue)
$resolvedResults = (Resolve-Path -LiteralPath $results).Path

for ($run = 1; $run -le $Repetitions; $run++) {
  $dockerArgs = @(
    "run", "--rm",
    "-e", "IMAGE_ID=$imageDigest",
    "--mount", "type=bind,source=$resolvedResults,target=/app/benchmarks/results"
  )
  if ($isLinuxHost) {
    $hostUid = (& id -u).Trim()
    if ($LASTEXITCODE -ne 0 -or $hostUid -notmatch '^\d+$') { throw "Cannot resolve Linux host UID" }
    $hostGid = (& id -g).Trim()
    if ($LASTEXITCODE -ne 0 -or $hostGid -notmatch '^\d+$') { throw "Cannot resolve Linux host GID" }
    $dockerArgs += @("--user", "${hostUid}:${hostGid}")
  }
  $dockerArgs += @(
    $Image, "benchmark",
    "--entities", "$Entities",
    "--batch-size", "$BatchSize",
    "--iterations", "$Iterations",
    "--warmups", "$Warmups",
    "--output", "/app/benchmarks/results/run-$run.json"
  )
  docker @dockerArgs | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Docker benchmark repetition $run failed" }
}

$rawPaths = @(Get-ChildItem -LiteralPath $results -Filter "run-*.json" -File | Sort-Object Name | ForEach-Object FullName)
$aggregateArgs = @(
  (Join-Path $PSScriptRoot "aggregate_results.py"),
  "--project", "feature-store-lite",
  "--metric", "online_read_latency_p95_ms",
  "--unit", "ms",
  "--signature-path", "proof.benchmark_signature",
  "--output", $summaryPath
)
foreach ($name in @(
  "online_read_p50_ms", "online_read_p95_ms", "online_read_p99_ms",
  "online_entity_values_per_second", "first_online_read_ms", "materialization_seconds",
  "point_in_time_match_rate", "future_leaks", "ttl_violations", "online_value_match_rate"
)) {
  $aggregateArgs += @("--summary-metric", $name)
}
$aggregateArgs += $rawPaths
python @aggregateArgs | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Benchmark aggregation failed" }

$producer = if ($env:GITHUB_ACTIONS -eq "true") { "github-actions" } else { "local" }
$command = "./tools/benchmark.ps1 -Entities $Entities -BatchSize $BatchSize -Iterations $Iterations -Warmups $Warmups -Repetitions $Repetitions"
python (Join-Path $PSScriptRoot "build_v2_evidence.py") `
  --root $root `
  --results-directory $results `
  --output $publication `
  --source-commit $sourceCommit `
  --image-ref $Image `
  --image-digest $imageDigest `
  --artifact-digest $artifactDigest `
  --hardware-class $HardwareClass `
  --entities $Entities `
  --batch-size $BatchSize `
  --iterations $Iterations `
  --warmups $Warmups `
  --repetitions $Repetitions `
  --producer $producer `
  --command $command
if ($LASTEXITCODE -ne 0) { throw "V2 evidence generation failed" }

Write-Host "benchmark_v2=$publication"
