"""School Feature Intelligence Agent public interface."""

from nma.agents.school_agent.discovery import SchoolAgentError
from nma.agents.school_agent.proposal import (
    SCHOOL_AGENT_SCHEMA,
    analyze_administrative_area,
)

__all__ = ["SCHOOL_AGENT_SCHEMA", "SchoolAgentError", "analyze_administrative_area"]
