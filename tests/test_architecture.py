import ast
from pathlib import Path

PACKAGE = Path("src/feature_store_lite")


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_domain_and_application_do_not_depend_on_feature_infrastructure():
    forbidden = {
        "boto3",
        "fastapi",
        "feast",
        "jsonschema",
        "pandas",
        "pyarrow",
        "redis",
    }
    for filename in ("domain.py", "fixture.py", "ports.py", "application.py"):
        assert imported_roots(PACKAGE / filename).isdisjoint(forbidden)


def test_feast_dependency_is_confined_to_adapter():
    feast_importers = [
        path.name
        for path in PACKAGE.glob("*.py")
        if "feast" in imported_roots(path)
    ]

    assert feast_importers == ["feast_adapter.py"]
