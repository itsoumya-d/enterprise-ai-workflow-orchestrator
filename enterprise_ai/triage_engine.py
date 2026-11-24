import re
from typing import List, Tuple
from enterprise_ai.models import IssueTicket, TriageAssessment, IssueCategory, SeverityLevel

RULES: List[Tuple[IssueCategory, SeverityLevel, str, List[str], str]] = [
    (
        IssueCategory.CI_RUNNER_FAILURE,
        SeverityLevel.CRITICAL,
        r"(exit code 137|out of memory|oomkilled|runner lost contact|job failed: killed)",
        ["ci-runner", "docker-executor", "compute"],
        "runbooks/ci/runner-oom-remediation.md"
    ),
    (
        IssueCategory.AUTH_PERMISSIONS,
        SeverityLevel.HIGH,
        r"(401 unauthorized|403 forbidden|permission denied|token expired|invalid credentials|rbac violation)",
        ["auth-gateway", "oauth-provider", "iam"],
        "runbooks/security/token-refresh-and-rbac.md"
    ),
    (
        IssueCategory.DATABASE_MIGRATION,
        SeverityLevel.HIGH,
        r"(lock timeout|deadlock detected|relation does not exist|migration failed|schema mismatch|foreign key constraint)",
        ["postgresql", "schema-migrator", "database"],
        "runbooks/data/migration-lock-resolution.md"
    ),
    (
        IssueCategory.API_RATE_LIMIT,
        SeverityLevel.MEDIUM,
        r"(429 too many requests|rate limit exceeded|throttled|quota exhausted)",
        ["api-gateway", "rate-limiter"],
        "runbooks/ops/rate-limit-backoff-scaling.md"
    ),
    (
        IssueCategory.STORAGE_REGISTRY,
        SeverityLevel.HIGH,
        r"(disk pressure|no space left on device|artifact upload failed|storage full|507 insufficient storage)",
        ["artifact-registry", "object-storage", "blob-store"],
        "runbooks/storage/volume-expansion-and-prune.md"
    )
]

class WorkflowTriageEngine:
    def triage_ticket(self, ticket: IssueTicket) -> TriageAssessment:
        combined = f"{ticket.title}\n{ticket.description}\n{ticket.raw_logs or ''}".lower()
        
        for category, severity, pattern, components, runbook in RULES:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                matched_token = match.group(0)
                return TriageAssessment(
                    ticket_id=ticket.ticket_id,
                    category=category,
                    severity=severity,
                    confidence=0.95,
                    detected_components=components,
                    suggested_runbook=runbook,
                    automated_action_eligible=severity in (SeverityLevel.MEDIUM, SeverityLevel.LOW),
                    reasoning=f"Matched diagnostic indicator '{matched_token}' mapped to {category.value}."
                )

        return TriageAssessment(
            ticket_id=ticket.ticket_id,
            category=IssueCategory.GENERAL_INQUIRY,
            severity=SeverityLevel.LOW,
            confidence=0.60,
            detected_components=["support-triage"],
            suggested_runbook="runbooks/general/standard-triage.md",
            automated_action_eligible=False,
            reasoning="No high-confidence operational failure patterns identified in telemetry or descriptions."
        )

    def triage_batch(self, tickets: List[IssueTicket]) -> List[TriageAssessment]:
        return [self.triage_ticket(t) for t in tickets]
