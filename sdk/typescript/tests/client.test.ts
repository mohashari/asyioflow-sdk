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
