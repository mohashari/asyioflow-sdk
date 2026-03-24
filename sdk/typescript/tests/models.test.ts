import {
  PriorityEnum,
  Priority,
  JobStatusEnum,
  JobSchema,
  SubmitJobRequestSchema,
  WorkflowStepSchema,
  WorkflowSchema,
} from "../src/models";

const NOW = "2026-01-01T00:00:00.000Z";

function makeJobData(overrides: Record<string, unknown> = {}) {
  return {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    type: "send-email",
    payload: { to: "x@y.com" },
    status: "completed",
    priority: 5,
    max_retries: 3,
    attempts: 1,
    error: null,
    run_at: null,
    created_at: NOW,
    updated_at: NOW,
    ...overrides,
  };
}

describe("Priority", () => {
  test("runtime values are correct", () => {
    expect(Priority.Low).toBe(1);
    expect(Priority.Normal).toBe(5);
    expect(Priority.High).toBe(10);
  });

  test("PriorityEnum validates valid values", () => {
    expect(PriorityEnum.parse(1)).toBe(1);
    expect(PriorityEnum.parse(5)).toBe(5);
    expect(PriorityEnum.parse(10)).toBe(10);
  });

  test("PriorityEnum rejects invalid value", () => {
    expect(() => PriorityEnum.parse(7)).toThrow();
  });
});

describe("JobStatusEnum", () => {
  test("accepts all valid statuses", () => {
    const statuses = ["pending", "queued", "running", "completed", "failed", "dead"];
    statuses.forEach((s) => expect(JobStatusEnum.parse(s)).toBe(s));
  });

  test("rejects unknown status", () => {
    expect(() => JobStatusEnum.parse("cancelled")).toThrow();
  });
});

describe("JobSchema", () => {
  test("parses valid job", () => {
    const job = JobSchema.parse(makeJobData());
    expect(job.id).toBe("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
    expect(job.status).toBe("completed");
    expect(job.priority).toBe(5);
  });

  test("error field absent is OK (nullish)", () => {
    const data = makeJobData();
    delete (data as Record<string, unknown>).error;
    const job = JobSchema.parse(data);
    expect(job.error == null).toBe(true);
  });

  test("run_at absent is OK (nullish)", () => {
    const data = makeJobData();
    delete (data as Record<string, unknown>).run_at;
    const job = JobSchema.parse(data);
    expect(job.run_at == null).toBe(true);
  });

  test("rejects job with missing required field", () => {
    const data = makeJobData();
    delete (data as Record<string, unknown>).id;
    expect(() => JobSchema.parse(data)).toThrow();
  });
});

describe("SubmitJobRequestSchema", () => {
  test("type only is valid", () => {
    const req = SubmitJobRequestSchema.parse({ type: "send-email" });
    expect(req.type).toBe("send-email");
  });

  test("empty type string is invalid", () => {
    expect(() => SubmitJobRequestSchema.parse({ type: "" })).toThrow();
  });
});

describe("WorkflowStepSchema", () => {
  test("minimal step", () => {
    const step = WorkflowStepSchema.parse({ name: "fetch", jobType: "fetch-data" });
    expect(step.name).toBe("fetch");
    expect(step.dependsOn).toEqual([]);
  });

  test("step with dependencies", () => {
    const step = WorkflowStepSchema.parse({
      name: "transform",
      jobType: "transform-data",
      dependsOn: ["fetch"],
    });
    expect(step.dependsOn).toEqual(["fetch"]);
  });
});

describe("WorkflowSchema", () => {
  test("parses valid workflow", () => {
    const wf = WorkflowSchema.parse({
      name: "pipeline",
      steps: [
        { name: "fetch", jobType: "fetch-data" },
        { name: "transform", jobType: "transform-data", dependsOn: ["fetch"] },
      ],
    });
    expect(wf.steps).toHaveLength(2);
  });
});

describe("Public exports", () => {
  test("all types and classes are re-exported from index", async () => {
    const mod = await import("../src/index");
    expect(mod.AysioFlowClient).toBeDefined();
    expect(mod.Priority).toBeDefined();
    expect(mod.AysioFlowError).toBeDefined();
    expect(mod.JobNotFoundError).toBeDefined();
  });
});
