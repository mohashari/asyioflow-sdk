import { z } from "zod";

// --- Priority ---
export const PriorityEnum = z.union([z.literal(1), z.literal(5), z.literal(10)]);
// Dual declaration: `Priority` as a type (for signatures) AND as a const (for runtime usage).
// TypeScript allows type + value to share a name.
export type Priority = z.infer<typeof PriorityEnum>;
export const Priority = { Low: 1, Normal: 5, High: 10 } as const satisfies Record<
  string,
  Priority
>;

// --- JobStatus ---
export const JobStatusEnum = z.enum([
  "pending",
  "queued",
  "running",
  "completed",
  "failed",
  "dead",
]);
export type JobStatus = z.infer<typeof JobStatusEnum>;

// --- Job (server response) ---
export const JobSchema = z.object({
  id: z.string().uuid(),
  type: z.string(),
  payload: z.record(z.unknown()).default({}),
  status: JobStatusEnum,
  priority: PriorityEnum,
  max_retries: z.number().int().min(0),
  attempts: z.number().int(),
  // Server may omit these fields (not just send null) — use .nullish()
  error: z.string().nullish(),
  run_at: z.string().datetime().nullish(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});
export type Job = z.infer<typeof JobSchema>;

// --- SubmitJobRequest (client input) ---
export const SubmitJobRequestSchema = z.object({
  type: z.string().min(1),
  payload: z.record(z.unknown()).optional(),
  priority: PriorityEnum.optional(),
  max_retries: z.number().int().min(0).optional(),
});
export type SubmitJobRequest = z.infer<typeof SubmitJobRequestSchema>;

// --- Workflow (camelCase — TypeScript client convention) ---
// Note: when submitting individual jobs, the SDK maps jobType → type and
// dependsOn is used only for orchestration order, not sent to the engine.
export const WorkflowStepSchema = z.object({
  name: z.string().min(1),
  jobType: z.string().min(1),
  payload: z.record(z.unknown()).default({}),
  dependsOn: z.array(z.string()).default([]),
});
export type WorkflowStep = z.infer<typeof WorkflowStepSchema>;

export const WorkflowSchema = z.object({
  name: z.string().min(1),
  steps: z.array(WorkflowStepSchema),
});
export type Workflow = z.infer<typeof WorkflowSchema>;
