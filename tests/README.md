# tests/ — zero-mock, real-data suite

See `../docs/testing_philosophy.md` for the philosophy. Every module in
`src/` has a matching test file; no mocks anywhere. Gate:
`uv run pytest tests/ --cov=src --cov-fail-under=90`.
