import json

from feature_store_lite import cli


def test_cli_passes_explicit_benchmark_shape(monkeypatch, tmp_path, capsys):
    output = tmp_path / "result.json"
    captured = {}

    def fake_run(output_path, **kwargs):
        captured["output"] = output_path
        captured.update(kwargs)
        return {"metric": "online_read_latency_p95_ms", "value": 1.25}

    monkeypatch.setattr(cli, "run_benchmark", fake_run)

    assert (
        cli.run(
            [
                "benchmark",
                "--entities",
                "16",
                "--batch-size",
                "4",
                "--iterations",
                "5",
                "--warmups",
                "2",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert captured["output"] == output
    assert captured["entity_count"] == 16
    assert captured["batch_size"] == 4
    assert captured["iterations"] == 5
    assert captured["warmups"] == 2
    assert json.loads(capsys.readouterr().out)["value"] == 1.25


def test_cli_defaults_to_benchmark(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "run_benchmark",
        lambda output, **kwargs: {"metric": "online_read_latency_p95_ms", "value": 1.0},
    )

    assert cli.run([]) == 0
    assert json.loads(capsys.readouterr().out)["value"] == 1.0
