import axios, { type AxiosInstance } from "axios";
import { createHttpTransport, type HttpTransport } from "./http";
import { JobSchema, type Job, type SubmitJobRequest, type Workflow } from "./models";
import { WorkflowStepFailedError, WorkflowTimeoutError } from "./exceptions";

const JOBS_URL = "/api/v1/jobs";
const JOB_URL = (id: string) => `/api/v1/jobs/${id}`;
const POLL_INTERVAL_MS = 2000;
const DEFAULT_WORKFLOW_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes

function validateDag(workflow: Workflow): void {
  const names = workflow.steps.map((s) => s.name);
  const seen = new Set<string>();
  for (const name of names) {
    if (seen.has(name)) throw new Error(`Duplicate workflow step name: "${name}"`);
    seen.add(name);
  }
  const nameSet = new Set(names);
  for (const step of workflow.steps) {
    for (const dep of step.dependsOn) {
      if (!nameSet.has(dep)) {
        throw new Error(`Step "${step.name}" depends on unknown step "${dep}"`);
      }
    }
  }
  // DFS cycle detection
  const deps = new Map(workflow.steps.map((s) => [s.name, s.dependsOn]));
  const visiting = new Set<string>();
  const visited = new Set<string>();
  function dfs(node: string): void {
    if (visiting.has(node)) throw new Error(`Cycle detected at step "${node}"`);
    if (visited.has(node)) return;
    visiting.add(node);
    for (const dep of deps.get(node) ?? []) dfs(dep);
    visiting.delete(node);
    visited.add(node);
  }
  for (const name of names) dfs(name);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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

  async submitWorkflow(workflow: Workflow): Promise<Record<string, Job>> {
    validateDag(workflow);
    const completed: Record<string, Job> = {};
    const pending = new Map(workflow.steps.map((s) => [s.name, s]));
    const deadline = Date.now() + this.workflowTimeoutMs;

    while (pending.size > 0) {
      const ready = [...pending.values()].filter((step) =>
        step.dependsOn.every((dep) => dep in completed),
      );

      for (const step of ready) {
        let job = await this.submitJob({ type: step.jobType, payload: step.payload });

        while (true) {
          if (Date.now() > deadline) {
            throw new WorkflowTimeoutError(step.name);
          }
          job = await this.getJob(job.id);
          if (job.status === "completed") {
            completed[step.name] = job;
            pending.delete(step.name);
            break;
          }
          if (job.status === "failed" || job.status === "dead") {
            throw new WorkflowStepFailedError(step.name, job.id, { ...completed });
          }
          await sleep(POLL_INTERVAL_MS);
        }
      }
    }

    return completed;
  }
}
