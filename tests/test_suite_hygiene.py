"""The no-mock claim, enforced instead of asserted.

`README.md` and `docs/testing_philosophy.md` claim this suite uses no mock
framework and that every substitution of a production callable is deliberate,
enumerated, and small. Those are claims *about the test suite*, so nothing in
the suite itself can check them by running normally — they are checked here by
reading the suite's own source.

Two gates:

1. no mock framework appears anywhere in ``src/`` or ``tests/``;
2. every ``monkeypatch.setattr`` call in ``tests/`` appears in the declared
   inventory below. Adding a new one fails this test until it is declared,
   which is the point: the previous revision's documented scan grepped only for
   mock-framework names and was structurally blind to ``monkeypatch``, so four
   production callables were being replaced under a "zero mocks, verified by
   scan" headline.
"""

from __future__ import annotations

import ast
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_SCANNED_DIRS = (_PACKAGE_ROOT / "src", _PACKAGE_ROOT / "tests")

# Assembled from fragments so that this scanner does not match itself and does
# not need to exempt its own file — an exemption would be a hole in the gate.
_MOCK_FRAMEWORK_TOKENS = (
    "Magic" + "Mock",
    "Async" + "Mock",
    "mocker" + ".patch",
    "unittest" + "." + "mock",
    "pytest_" + "mock",
)

#: Every sanctioned ``monkeypatch.setattr`` in the suite: (file, target, attribute).
#:
#: Three of the four replace a module-level *callable* with a trivial real
#: callable that returns a real empty value, to drive an empty-input guard that
#: no real configuration can reach. The fourth swaps a string constant. None
#: installs an object whose behaviour is scripted by the test, and none records
#: or asserts on calls.
_DECLARED_SETATTR: frozenset[tuple[str, str, str]] = frozenset(
    {
        # unregistered-provider CLI path: swaps a module-level string constant.
        ("test_cli.py", "cli", "SLUG"),
        # "library grew a new isotope" path: real dict of real IsotopeProfiles.
        ("test_isotope_profiles.py", "canonical_module", "isotope_library"),
        # empty-library guard in generate_variables(): returns a real empty tuple.
        ("test_manuscript_variables.py", "mv", "library_names"),
        # empty-library guard in _library_line_bounds(): builtin dict, no lines.
        ("test_manuscript_variables.py", "mv", "isotope_library"),
    }
)


def _python_files() -> list[Path]:
    files = [path for directory in _SCANNED_DIRS for path in directory.rglob("*.py")]
    assert files, "hygiene scan found no Python files — the scan paths are wrong"
    return files


def test_no_mock_framework_in_src_or_tests() -> None:
    """No mock framework anywhere. Lexical, over every file, not a sampled grep."""
    offenders: list[str] = []
    for path in _python_files():
        text = path.read_text(encoding="utf-8")
        for token in _MOCK_FRAMEWORK_TOKENS:
            if token in text:
                offenders.append(f"{path.relative_to(_PACKAGE_ROOT)}: {token}")
    assert not offenders, f"mock framework used: {offenders}"


def _setattr_sites(path: Path) -> set[tuple[str, str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    sites: set[tuple[str, str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "setattr"):
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "monkeypatch"):
            continue
        target = func.value.id if not node.args else ast.unparse(node.args[0])
        attribute = ast.unparse(node.args[1]).strip("'\"") if len(node.args) > 1 else "<unknown>"
        sites.add((path.name, target, attribute))
    return sites


def test_monkeypatch_setattr_inventory_is_exact() -> None:
    """Every production-callable substitution is declared; nothing else is allowed.

    This is what makes the no-mock claim checkable rather than aspirational. An
    undeclared substitution fails here with its own coordinates; a declared one
    that disappears also fails, so the inventory cannot rot into a stale list.
    """
    found: set[tuple[str, str, str]] = set()
    for path in sorted((_PACKAGE_ROOT / "tests").rglob("*.py")):
        found |= _setattr_sites(path)
    undeclared = sorted(found - _DECLARED_SETATTR)
    vanished = sorted(_DECLARED_SETATTR - found)
    assert not undeclared, (
        "undeclared monkeypatch.setattr — declare it in _DECLARED_SETATTR with a "
        f"comment saying what real object it installs and why: {undeclared}"
    )
    assert not vanished, f"declared monkeypatch.setattr no longer present: {vanished}"


def test_declared_inventory_is_small() -> None:
    """A ceiling, so the sanctioned-substitution list cannot quietly grow into a habit."""
    assert len(_DECLARED_SETATTR) <= 4, (
        "the monkeypatch inventory grew; either the substitution is avoidable with a "
        "real object, or this ceiling and the README claim must both be revised"
    )
