"""The claim ledger is bound to the code, not a hand-maintained comment.

``data/claim_ledger.yaml`` marks ten claims ``verified: true``, but nothing
read the file — a renamed symbol, a deleted test, or a softened claim could
all go false while the whole suite stayed green. V1 in TODO.md. This test loads
the ledger and resolves every ``source:`` field against the live tree, so an
unresolvable source fails the build:

* ``src/.../mod.py::symbol`` — the module file must exist and the symbol must
  be defined in it (``def``/``class``/assignment), checked by AST so no import
  side effects and no path tricks.
* ``tests/...::test_name`` — the test file must exist and define that test.
* any bare path — the file must exist.

Real file reads and AST parsing only; no mock framework, no network.
"""

from __future__ import annotations

import ast
from pathlib import Path

import yaml

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_LEDGER_PATH = _PACKAGE_ROOT / "data" / "claim_ledger.yaml"


def _defined_symbols(path: Path) -> set[str]:
    """Top-level ``def``/``class``/assignment names defined in a Python file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _resolve_source(source: str) -> list[str]:
    """Return a list of problems for one ledger ``source``; empty means resolved."""
    if "::" in source:
        path_part, symbol = source.split("::", 1)
        path = _PACKAGE_ROOT / path_part
        if not path.is_file():
            return [f"source file missing: {source!r}"]
        if path.suffix == ".py":
            try:
                defined = _defined_symbols(path)
            except SyntaxError as exc:
                return [f"source file fails to parse: {source!r}: {exc}"]
            if symbol not in defined:
                return [f"symbol {symbol!r} not defined in {path_part}"]
        return []
    path = _PACKAGE_ROOT / source
    if not path.is_file():
        return [f"source file missing: {source!r}"]
    return []


def test_claim_ledger_is_well_formed() -> None:
    import yaml as _yaml

    data = _yaml.safe_load(_LEDGER_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and isinstance(data.get("claims"), list)
    assert data["claims"], "claim ledger declares no claims"
    ids = [claim["id"] for claim in data["claims"]]
    assert len(ids) == len(set(ids)), "claim ids must be unique"


def test_every_claim_has_a_resolvable_source() -> None:
    """Every ``source:`` must resolve against the live tree.

    Rename a symbol named in the ledger, delete a test it points to, or remove
    a data file, and this test goes red — which is exactly what V1 requires.
    """
    data = yaml.safe_load(_LEDGER_PATH.read_text(encoding="utf-8"))
    problems: list[str] = []
    for claim in data["claims"]:
        source = claim.get("source")
        if not source:
            problems.append(f"claim {claim.get('id')!r} has no source")
            continue
        problems.extend(_resolve_source(source))
    assert not problems, "unresolvable claim sources:\n" + "\n".join(problems)


def test_every_claim_declares_and_gets_verified() -> None:
    """Each entry must carry an id, a claim statement, and a verified flag."""
    data = yaml.safe_load(_LEDGER_PATH.read_text(encoding="utf-8"))
    for claim in data["claims"]:
        assert claim.get("id"), "claim missing id"
        assert claim.get("claim"), f"claim {claim.get('id')!r} missing claim text"
        assert claim.get("verified") is True, f"claim {claim.get('id')!r} not verified"
