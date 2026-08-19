import pytest

from omniagent.adapters import (
    build_lead_search_request,
    lead_to_revenue_opportunity,
    search_result_to_opportunities,
)


def test_build_lead_search_request_normalizes_payload():
    request = build_lead_search_request("req-1", "  abogados ", " Madrid ", 5)

    assert request.task_type == "lead_search"
    assert request.payload == {"query": "abogados", "location": "Madrid", "limit": 5}
    assert request.trust_required is False


def test_build_lead_search_request_rejects_invalid_limit():
    with pytest.raises(ValueError):
        build_lead_search_request("req-1", "abogados", limit=61)


def test_lead_to_revenue_opportunity_has_stable_identity():
    lead = {
        "name": "Empresa Real",
        "email": "CONTACTO@EMPRESA.ES",
        "phone": "+34 600 000 001",
        "address": "Calle Real 1",
        "website": "https://empresa.es",
        "source": "LIVE_HYBRID",
    }

    first = lead_to_revenue_opportunity(lead, monthly_fee=300)
    second = lead_to_revenue_opportunity(lead, monthly_fee=300)

    assert first == second
    assert first["stage"] == "lead"
    assert first["monthly_fee"] == 300.0
    assert first["email"] == "contacto@empresa.es"
    assert first["phone"] == "34600000001"


def test_search_result_to_opportunities_maps_all_leads():
    result = {"leads": [{"name": "A"}, {"name": "B"}]}

    opportunities = search_result_to_opportunities(result, monthly_fee=450)

    assert len(opportunities) == 2
    assert {item["name"] for item in opportunities} == {"A", "B"}
    assert all(item["monthly_fee"] == 450.0 for item in opportunities)


def test_revenue_adapter_rejects_unknown_stage():
    with pytest.raises(ValueError):
        lead_to_revenue_opportunity({"name": "A"}, stage="contacted")
