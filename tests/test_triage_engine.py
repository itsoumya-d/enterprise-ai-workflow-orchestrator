import pytest
from enterprise_ai.models import IssueTicket, IssueCategory, SeverityLevel
from enterprise_ai.triage_engine import WorkflowTriageEngine

@pytest.fixture
def engine():
    return WorkflowTriageEngine()

def test_triage_ci_runner_oom_failure(engine):
    ticket = IssueTicket(
        ticket_id="INC-101",
        title="Pipeline job failed unexpectedly in integration stage",
        description="Build runner abruptly terminated during compilation step.",
        raw_logs="ERROR: Job failed: killed (exit code 137, OOMKilled by cgroup kernel controller)"
    )
    res = engine.triage_ticket(ticket)
    assert res.category == IssueCategory.CI_RUNNER_FAILURE
    assert res.severity == SeverityLevel.CRITICAL
    assert res.confidence >= 0.90
    assert "ci-runner" in res.detected_components
    assert "runner-oom-remediation.md" in res.suggested_runbook

def test_triage_auth_token_expiration(engine):
    ticket = IssueTicket(
        ticket_id="INC-102",
        title="Deployment agent unable to push release manifest",
        description="Worker reported 401 Unauthorized when invoking internal registry API.",
        raw_logs="HTTP/2.0 401 Unauthorized: token expired at epoch 1700000000"
    )
    res = engine.triage_ticket(ticket)
    assert res.category == IssueCategory.AUTH_PERMISSIONS
    assert res.severity == SeverityLevel.HIGH
    assert "auth-gateway" in res.detected_components

def test_triage_database_migration_lock(engine):
    ticket = IssueTicket(
        ticket_id="INC-103",
        title="Schema migration blocked on production release",
        description="Alembic step unable to acquire exclusive table lock.",
        raw_logs="psycopg2.OperationalError: lock timeout while executing ALTER TABLE orders"
    )
    res = engine.triage_ticket(ticket)
    assert res.category == IssueCategory.DATABASE_MIGRATION
    assert res.severity == SeverityLevel.HIGH
    assert "postgresql" in res.detected_components

def test_triage_rate_limit_backoff(engine):
    ticket = IssueTicket(
        ticket_id="INC-104",
        title="Bulk notification webhook delays",
        description="External endpoints returning 429 Too Many Requests due to burst limit."
    )
    res = engine.triage_ticket(ticket)
    assert res.category == IssueCategory.API_RATE_LIMIT
    assert res.severity == SeverityLevel.MEDIUM
    assert res.automated_action_eligible is True

def test_triage_general_inquiry_fallback(engine):
    ticket = IssueTicket(
        ticket_id="INC-105",
        title="Question regarding upcoming quarterly team offsite",
        description="Where can I find the shared calendar for travel arrangements?"
    )
    res = engine.triage_ticket(ticket)
    assert res.category == IssueCategory.GENERAL_INQUIRY
    assert res.severity == SeverityLevel.LOW
    assert res.confidence == 0.60
    assert res.automated_action_eligible is False

def test_triage_batch_processing(engine):
    tickets = [
        IssueTicket(ticket_id="B-1", title="Disk full on cache node", description="no space left on device"),
        IssueTicket(ticket_id="B-2", title="General question", description="Docs link request")
    ]
    results = engine.triage_batch(tickets)
    assert len(results) == 2
    assert results[0].category == IssueCategory.STORAGE_REGISTRY
    assert results[1].category == IssueCategory.GENERAL_INQUIRY
