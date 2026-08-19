"""Deterministic adapters between workforce modules.

These adapters normalize data only. They do not send messages, call prospects,
or create billing transactions.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .workforce import Evidence, ExecutionRequest


def build_lead_search_request(
    request_id: str,
    query: str,
    location: str = "",
    limit: int = 20,
) -> ExecutionRequest:
    """Create a workforce request for Omniscraper's search API."""

    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 60:
        raise ValueError("limit must be between 1 and 60")
    return ExecutionRequest(
        request_id=request_id,
        task_type="lead_search",
        payload={"query": query.strip(), "location": location.strip(), "limit": limit},
        trust_required=False,
        evidence=(Evidence("omniscraper", "search-request", f"query={query.strip()}"),),
    )


def lead_to_revenue_opportunity(
    lead: dict[str, Any],
    *,
    monthly_fee: float = 0.0,
    stage: str = "lead",
) -> dict[str, Any]:
    """Map one normalized Omniscraper lead to Revenue OS's local schema."""

    if stage not in {"lead", "qualified", "proposal", "pilot", "active", "lost"}:
        raise ValueError(f"unsupported revenue stage: {stage}")
    if monthly_fee < 0:
        raise ValueError("monthly_fee must be non-negative")

    name = str(lead.get("name", "")).strip()
    email = str(lead.get("email", "")).strip().lower()
    phone = re.sub(r"\D", "", str(lead.get("phone", "")))
    address = str(lead.get("address", "")).strip()
    identity = email or phone or f"{name}|{address}"
    opportunity_id = "lead-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]

    return {
        "id": opportunity_id,
        "stage": stage,
        "monthly_fee": round(float(monthly_fee), 2),
        "name": name,
        "email": email,
        "phone": phone,
        "address": address,
        "website": str(lead.get("website", "")).strip(),
        "source": str(lead.get("source", "omniscraper")),
    }


def search_result_to_opportunities(
    search_result: dict[str, Any], *, monthly_fee: float = 0.0
) -> list[dict[str, Any]]:
    """Convert Omniscraper's ``leads`` response to Revenue OS records."""

    leads = search_result.get("leads", [])
    if not isinstance(leads, list):
        raise ValueError("search_result.leads must be a list")
    return [lead_to_revenue_opportunity(lead, monthly_fee=monthly_fee) for lead in leads]
