import type { Job } from "./models";

export class AysioFlowError extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class JobNotFoundError extends AysioFlowError {} // HTTP 404
export class ValidationError extends AysioFlowError {}  // HTTP 400
export class ServerError extends AysioFlowError {}      // HTTP 5xx

export class WorkflowStepFailedError extends AysioFlowError {
  constructor(
    public readonly stepName: string,
    public readonly jobId: string,
    public readonly completedSteps: Record<string, Job>,
  ) {
    super(`Workflow aborted: step "${stepName}" (job ${jobId}) failed`);
  }
}

export class WorkflowTimeoutError extends AysioFlowError {
  constructor(public readonly stepName: string) {
    super(`Workflow timeout waiting for step "${stepName}"`);
  }
}
