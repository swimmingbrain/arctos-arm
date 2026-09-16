# Contributing

Bug reports and pull requests are welcome, especially anything learned on a
real arm: gear ratios that differ, directions, homing parameters.

Before a pull request:

```bash
uv sync --group dev
uv run ruff format src tests
uv run ruff check src tests
uv run mypy src
uv run pytest
```

All tests run in the simulation, nothing has to be plugged in. If you change
the CAN protocol please quote the section of the MKS manual you used.

Commit messages follow `type: message` with the usual types (feat, fix,
docs, test, refactor, chore).
