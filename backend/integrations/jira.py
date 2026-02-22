"""Jira integration — DEPRECATED in V2 Architecture.

In V2, all Jira operations are handled by n8n workflows.
This module is kept as a legacy stub for backward compatibility.
The actual Jira issue creation, linking, and commenting is now
performed by n8n Workflow 1 (Intake, Queueing, and Jira Routing).

See: backend/n8n_workflows/n8n_workflow_1_intake_jira_routing.json
"""
from __future__ import annotations

import logging
import warnings
from typing import List, Optional

logger = logging.getLogger(__name__)

_DEPRECATION_MSG = (
    "Direct Jira API calls from Python are deprecated in V2. "
    "Jira operations are now handled by n8n workflows."
)


def create_jira_issue(
    summary: str,
    description: str,
    priority: str,
    labels: List[str],
) -> Optional[str]:
    """DEPRECATED: Jira issues are now created by n8n Workflow 1.

    This stub returns a mock key for any code that still references it.
    """
    warnings.warn(_DEPRECATION_MSG, DeprecationWarning, stacklevel=2)
    logger.warning(_DEPRECATION_MSG)
    return "DEPRECATED-V2"
