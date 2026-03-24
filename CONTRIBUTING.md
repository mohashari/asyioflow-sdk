# Contributing to asyioflow-sdk

## Setup

```bash
# Python
cd sdk/python && pip install -e ".[dev]"

# TypeScript
cd sdk/typescript && npm install
```

## Running Tests

```bash
# Python
cd sdk/python && pytest -v

# TypeScript
cd sdk/typescript && npm test
```

## Code Style

- Python: `ruff check sdk/python/asyioflow`
- TypeScript: `npx tsc --noEmit` (strict mode)

## Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Write tests first (TDD)
4. Open a PR against `main`
