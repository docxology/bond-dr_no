# tests/ — real-data suite, no mock framework

See `../docs/testing_philosophy.md` for the philosophy, including the four
declared `monkeypatch.setattr` substitutions and why they are not mocks. Every
module in `src/` has a matching test file; `test_suite_hygiene.py` enforces the
no-mock claim by reading this directory's own source. Gate:
`uv run pytest tests/ --cov=src --cov-fail-under=90`.
