# Changelog

## [0.1.0] - 2026-03-24

### Added
- Python SDK: `AysioFlow` (sync) + `AsyncAysioFlow` (async) clients
- Python SDK: `submit_workflow()` DAG orchestration with dependency order and timeout
- TypeScript SDK: `AysioFlowClient` with `submitJob`, `getJob`, `cancelJob`, `submitWorkflow`
- Shared JSON Schema (`schema/asyioflow.schema.json`) for workflow type definitions
- GitHub Actions CI (Python 3.10/3.11/3.12, Node 18/20) + release workflows (PyPI + NPM)
- Published to PyPI (`asyioflow-sdk`) and NPM (`@asyioflow/sdk`)
