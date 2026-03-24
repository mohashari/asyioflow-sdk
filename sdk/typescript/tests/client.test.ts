import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import { AysioFlowClient } from "../src/client";
import { Priority } from "../src/models";
import { JobNotFoundError, ValidationError } from "../src/exceptions";

const BASE_URL = "http://test-engine:8080";
const NOW = "2026-01-01T00:00:00.000Z";

function makeJobData(overrides: Record<string, unknown> = {}) {
  return {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    type: "send-email",
    payload: {},
    status: "pending",
    priority: 5,
    max_retries: 3,
    attempts: 0,
    error: null,
    run_at: null,
    created_at: NOW,
    updated_at: NOW,
    ...overrides,
  };
}

describe("AysioFlowClient — submitJob", () => {
  test("returns Job on 201", async () => {
    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    mock.onPost("/api/v1/jobs").reply(201, makeJobData());

    const client = new AysioFlowClient({ baseUrl: BASE_URL, _axiosInstance: axiosInst });
    const job = await client.submitJob({ type: "send-email" });

    expect(job.id).toBe("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    expect(job.status).toBe("pending");
    mock.restore();
  });

  test("400 throws ValidationError", async () => {
    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    mock.onPost("/api/v1/jobs").reply(400, "type required");

    const client = new AysioFlowClient({ baseUrl: BASE_URL, _axiosInstance: axiosInst });
    await expect(client.submitJob({ type: "send-email" })).rejects.toBeInstanceOf(ValidationError);
    mock.restore();
  });
});

describe("AysioFlowClient — getJob", () => {
  test("returns Job on 200", async () => {
    const jobId = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    mock.onGet(`/api/v1/jobs/${jobId}`).reply(200, makeJobData({ id: jobId, status: "completed" }));

    const client = new AysioFlowClient({ baseUrl: BASE_URL, _axiosInstance: axiosInst });
    const job = await client.getJob(jobId);

    expect(job.status).toBe("completed");
    mock.restore();
  });

  test("404 throws JobNotFoundError", async () => {
    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    mock.onGet("/api/v1/jobs/missing").reply(404, "not found");

    const client = new AysioFlowClient({ baseUrl: BASE_URL, _axiosInstance: axiosInst });
    await expect(client.getJob("missing")).rejects.toBeInstanceOf(JobNotFoundError);
    mock.restore();
  });
});

describe("AysioFlowClient — cancelJob", () => {
  test("resolves on 204", async () => {
    const jobId = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";
    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    mock.onDelete(`/api/v1/jobs/${jobId}`).reply(204);

    const client = new AysioFlowClient({ baseUrl: BASE_URL, _axiosInstance: axiosInst });
    await client.cancelJob(jobId); // no throw
    mock.restore();
  });

  test("404 throws JobNotFoundError", async () => {
    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    mock.onDelete("/api/v1/jobs/missing").reply(404, "not found");

    const client = new AysioFlowClient({ baseUrl: BASE_URL, _axiosInstance: axiosInst });
    await expect(client.cancelJob("missing")).rejects.toBeInstanceOf(JobNotFoundError);
    mock.restore();
  });
});

import type { Workflow } from "../src/models";
import { WorkflowStepFailedError, WorkflowTimeoutError } from "../src/exceptions";

function makeCompletedJob(id: string, type: string) {
  return makeJobData({ id, type, status: "completed" });
}

function makeFailedJob(id: string, type: string) {
  return makeJobData({ id, type, status: "failed", error: "crash" });
}

describe("AysioFlowClient — submitWorkflow", () => {
  test("single-step workflow returns results", async () => {
    const fetchId = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb";
    const wf: Workflow = {
      name: "simple",
      steps: [{ name: "fetch", jobType: "fetch-data", payload: {}, dependsOn: [] }],
    };

    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    mock.onPost("/api/v1/jobs").reply(201, makeCompletedJob(fetchId, "fetch-data"));
    mock.onGet(`/api/v1/jobs/${fetchId}`).reply(200, makeCompletedJob(fetchId, "fetch-data"));

    const client = new AysioFlowClient({ baseUrl: BASE_URL, _axiosInstance: axiosInst });
    const results = await client.submitWorkflow(wf);

    expect(results["fetch"].id).toBe(fetchId);
    mock.restore();
  });

  test("sequential workflow respects dependency order", async () => {
    const fetchId = "cccccccc-cccc-cccc-cccc-cccccccccccc";
    const transformId = "dddddddd-dddd-dddd-dddd-dddddddddddd";
    const wf: Workflow = {
      name: "pipeline",
      steps: [
        { name: "fetch", jobType: "fetch-data", payload: {}, dependsOn: [] },
        { name: "transform", jobType: "transform-data", payload: {}, dependsOn: ["fetch"] },
      ],
    };

    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    let postCount = 0;
    mock.onPost("/api/v1/jobs").reply(() => {
      postCount++;
      if (postCount === 1) return [201, makeCompletedJob(fetchId, "fetch-data")];
      return [201, makeCompletedJob(transformId, "transform-data")];
    });
    mock.onGet(`/api/v1/jobs/${fetchId}`).reply(200, makeCompletedJob(fetchId, "fetch-data"));
    mock.onGet(`/api/v1/jobs/${transformId}`).reply(200, makeCompletedJob(transformId, "transform-data"));

    const client = new AysioFlowClient({ baseUrl: BASE_URL, _axiosInstance: axiosInst });
    const results = await client.submitWorkflow(wf);

    expect(Object.keys(results).sort()).toEqual(["fetch", "transform"]);
    mock.restore();
  });

  test("failed step throws WorkflowStepFailedError with partial results", async () => {
    const fetchId = "ffffffff-ffff-ffff-ffff-ffffffffffff";
    const transformId = "00000000-0000-0000-0000-000000000000";
    const wf: Workflow = {
      name: "pipeline",
      steps: [
        { name: "fetch", jobType: "fetch-data", payload: {}, dependsOn: [] },
        { name: "transform", jobType: "transform-data", payload: {}, dependsOn: ["fetch"] },
      ],
    };

    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    let postCount = 0;
    mock.onPost("/api/v1/jobs").reply(() => {
      postCount++;
      if (postCount === 1) return [201, makeCompletedJob(fetchId, "fetch-data")];
      return [201, makeFailedJob(transformId, "transform-data")];
    });
    mock.onGet(`/api/v1/jobs/${fetchId}`).reply(200, makeCompletedJob(fetchId, "fetch-data"));
    mock.onGet(`/api/v1/jobs/${transformId}`).reply(200, makeFailedJob(transformId, "transform-data"));

    const client = new AysioFlowClient({ baseUrl: BASE_URL, _axiosInstance: axiosInst });
    await expect(client.submitWorkflow(wf)).rejects.toBeInstanceOf(WorkflowStepFailedError);

    postCount = 0; // reset so second call sees the same mock state
    try {
      await client.submitWorkflow(wf);
    } catch (err) {
      if (err instanceof WorkflowStepFailedError) {
        expect(err.stepName).toBe("transform");
        expect("fetch" in err.completedSteps).toBe(true);
      }
    }
    mock.restore();
  });

  test("timeout throws WorkflowTimeoutError", async () => {
    const fetchId = "11111111-2222-3333-4444-555555555555";
    const wf: Workflow = {
      name: "simple",
      steps: [{ name: "fetch", jobType: "fetch-data", payload: {}, dependsOn: [] }],
    };

    const runningJob = makeJobData({ id: fetchId, type: "fetch-data", status: "running" });

    const axiosInst = axios.create({ baseURL: BASE_URL });
    const mock = new MockAdapter(axiosInst);
    mock.onPost("/api/v1/jobs").reply(201, runningJob);
    mock.onGet(`/api/v1/jobs/${fetchId}`).reply(200, runningJob);

    const client = new AysioFlowClient({
      baseUrl: BASE_URL,
      _axiosInstance: axiosInst,
      workflowTimeoutMs: 0, // immediate timeout
    });
    await expect(client.submitWorkflow(wf)).rejects.toBeInstanceOf(WorkflowTimeoutError);
    mock.restore();
  });
});
