"""Deterministic adapters between workforce modules.

These adapters normalize data only. They do not send messages, call prospects,
or create billing transactions. Keep raw search terms out of audit evidence.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from .workforce import Evidence, ExecutionRequest

_REVENUE_STAGES = {"lead", "qualified", "proposal", "pilot", "active", "lost"}


def build_lead_search_request(
    request_id: str,
    query: str,
    location: str = "",
    limit: int = 20,
) -> ExecutionRequest:
    """Create a workforce request for Omniscraper's search API."""
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be a non-empty string")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if not isinstance(location, str):
        raise ValueError("location must be a string")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 60:
        raise ValueError("limit must be an integer between 1 and 60")

    clean_query = query.strip()
    return ExecutionRequest(
        request_id=request_id.strip(),
        task_type="lead_search",
        payload={"query": clean_query, "location": location.strip(), "limit": limit},
        trust_required=False,
        evidence=(
            Evidence(
                "omniscraper",
                "search-request",
                f"query supplied ({len(clean_query)} characters)",
            ),
        ),
    )


def _non_negative_fee(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("monthly_fee must be a finite, non-negative amount")
    try:
        fee = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("monthly_fee must be a finite, non-negative amount") from None
    if not math.isfinite(fee) or fee < 0:
        raise ValueError("monthly_fee must be a finite, non-negative amount")
    return round(fee, 2)


def lead_to_revenue_opportunity(
    lead: dict[str, Any],
    *,
    monthly_fee: float = 0.0,
    stage: str = "lead",
) -> dict[str, Any]:
    """Map one normalized Omniscraper lead to Revenue OS's local schema."""
    if not isinstance(lead, dict):
        raise ValueError("lead must be a mapping")
    if not isinstance(stage, str) or stage not in _REVENUE_STAGES:
        raise ValueError(f"unsupported revenue stage: {stage}")
    fee = _non_negative_fee(monthly_fee)

    name = str(lead.get("name", "") or "").strip()
    email = str(lead.get("email", "") or "").strip().lower()
    phone = re.sub(r"\D", "", str(lead.get("phone", "") or ""))
    address = str(lead.get("address", "") or "").strip()
    website = str(lead.get("website", "") or "").strip()
    external_id = str(lead.get("id", "") or "").strip()

    if email:
        identity = f"email:{email}"
    elif phone:
        identity = f"phone:{phone}"
    elif external_id:
        identity = f"id:{external_id}"
    elif website:
        identity = f"website:{website.casefold()}"
    elif name or address:
        identity = f"name-address:{name.casefold()}|{address.casefold()}"
    else:
        raise ValueError("lead needs at least an email, phone, id, website, name, or address")

    opportunity_id = "lead-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    source = lead.get("source", "omniscraper")
    if not isinstance(source, str):
        source = "omniscraper"

    return {
        "id": opportunity_id,
        "stage": stage,
        "monthly_fee": fee,
        "name": name,
        "email": email,
        "phone": phone,
        "address": address,
        "website": website,
        "source": source.strip() or "omniscraper",
    }


def search_result_to_opportunities(
    search_result: dict[str, Any], *, monthly_fee: float = 0.0
) -> list[dict[str, Any]]:
    """Convert Omniscraper's ``leads`` response to Revenue OS records."""
    if not isinstance(search_result, dict):
        raise ValueError("search_result must be a mapping")
    leads = search_result.get("leads", [])
    if not isinstance(leads, list):
        raise ValueError("search_result.leads must be a list")
    return [lead_to_revenue_opportunity(lead, monthly_fee=monthly_fee) for lead in leads]
