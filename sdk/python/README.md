# asyioflow-sdk (Python)

Python client for the [AysioFlow](https://github.com/mohashari/asyioflow-engine) workflow engine.

## Installation

```bash
pip install asyioflow-sdk
```

## Quick Start

```python
from asyioflow import AysioFlow, AsyncAysioFlow
from asyioflow import SubmitJobRequest, Workflow, WorkflowStep

# Sync
client = AysioFlow(base_url="http://localhost:8080")
job = client.submit(SubmitJobRequest(type="send-email", payload={"to": "x@y.com"}))
print(job.id, job.status)

# Async
async with AsyncAysioFlow(base_url="http://localhost:8080") as client:
    job = await client.submit(SubmitJobRequest(type="send-email"))

# Workflow (DAG)
wf = Workflow(name="pipeline", steps=[
    WorkflowStep(name="fetch", job_type="fetch-data"),
    WorkflowStep(name="transform", job_type="transform-data", depends_on=["fetch"]),
])
results = client.submit_workflow(wf)
```
