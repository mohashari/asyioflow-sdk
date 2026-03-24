import axios, { type AxiosInstance } from "axios";
import { createHttpTransport, type HttpTransport } from "./http";
import { JobSchema, type Job, type SubmitJobRequest, type Workflow } from "./models";
import { WorkflowStepFailedError, WorkflowTimeoutError } from "./exceptions";

const JOBS_URL = "/api/v1/jobs";
const JOB_URL = (id: string) => `/api/v1/jobs/${id}`;
const POLL_INTERVAL_MS = 2000;
const DEFAULT_WORKFLOW_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes

export interface AysioFlowClientOptions {
  baseUrl: string;
  timeout?: number;
  apiKey?: string;
  workflowTimeoutMs?: number;
  /** @internal — inject axios instance for testing */
  _axiosInstance?: AxiosInstance;
}

export class AysioFlowClient {
  private readonly transport: HttpTransport;
  private readonly workflowTimeoutMs: number;

  constructor(opts: AysioFlowClientOptions) {
    const axiosInst =
      opts._axiosInstance ??
      axios.create({
        baseURL: opts.baseUrl,
        timeout: opts.timeout ?? 30_000,
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(opts.apiKey ? { "X-Api-Key": opts.apiKey } : {}),
        },
      });
    this.transport = createHttpTransport(axiosInst);
    this.workflowTimeoutMs = opts.workflowTimeoutMs ?? DEFAULT_WORKFLOW_TIMEOUT_MS;
  }

  async submitJob(req: SubmitJobRequest): Promise<Job> {
    const data = await this.transport.post(JOBS_URL, req);
    return JobSchema.parse(data);
  }

  async getJob(jobId: string): Promise<Job> {
    const data = await this.transport.get(JOB_URL(jobId));
    return JobSchema.parse(data);
  }

  async cancelJob(jobId: string): Promise<void> {
    await this.transport.delete(JOB_URL(jobId));
  }
}
