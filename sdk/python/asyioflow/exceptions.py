from __future__ import annotations


class AysioFlowError(Exception):
    """Base exception for all AysioFlow SDK errors."""


class JobNotFoundError(AysioFlowError):
    """Raised when the engine returns HTTP 404."""


class ValidationError(AysioFlowError):
    """Raised when the engine returns HTTP 400."""


class ServerError(AysioFlowError):
    """Raised when the engine returns HTTP 5xx."""


class WorkflowStepFailedError(AysioFlowError):
    """Raised when a workflow step reaches failed or dead status.

    Attributes:
        step_name: Name of the failed step.
        job_id: ID of the failed job.
        completed_steps: Partial results for steps that completed before failure.
    """

    def __init__(self, step_name: str, job_id: str, completed_steps: dict) -> None:
        super().__init__(
            f'Workflow aborted: step "{step_name}" (job {job_id}) failed'
        )
        self.step_name = step_name
        self.job_id = job_id
        self.completed_steps = completed_steps


class WorkflowTimeoutError(AysioFlowError):
    """Raised when a workflow step exceeds the configured timeout.

    Attributes:
        step_name: Name of the step that timed out.
    """

    def __init__(self, step_name: str) -> None:
        super().__init__(f'Workflow timeout waiting for step "{step_name}"')
        self.step_name = step_name
