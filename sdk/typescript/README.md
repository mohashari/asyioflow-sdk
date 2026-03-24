# @asyioflow/sdk (TypeScript)

TypeScript client for the [AysioFlow](https://github.com/mohashari/asyioflow-engine) workflow engine.

## Installation

```bash
npm install @asyioflow/sdk
```

## Quick Start

```typescript
import { AysioFlowClient, Priority } from "@asyioflow/sdk";
import type { Job, Workflow } from "@asyioflow/sdk";

const client = new AysioFlowClient({ baseUrl: "http://localhost:8080" });

// Submit a job
const job = await client.submitJob({ type: "send-email", payload: { to: "x@y.com" } });
console.log(job.id, job.status);

// Workflow (DAG)
const wf: Workflow = {
  name: "pipeline",
  steps: [
    { name: "fetch", jobType: "fetch-data", payload: {}, dependsOn: [] },
    { name: "transform", jobType: "transform-data", payload: {}, dependsOn: ["fetch"] },
  ],
};
const results = await client.submitWorkflow(wf);
```
