import pytest


@pytest.fixture(autouse=True)
def force_deterministic_agent_provider(monkeypatch):
    monkeypatch.setenv("AGENT_DECISION_PROVIDER", "development")