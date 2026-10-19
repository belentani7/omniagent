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


def test_revenue_adapter_rejects_non_finite_fee_and_missing_identity():
    with pytest.raises(ValueError, match="monthly_fee"):
        lead_to_revenue_opportunity({"name": "A"}, monthly_fee=float("nan"))
    with pytest.raises(ValueError, match="at least an email"):
        lead_to_revenue_opportunity({})


def test_request_validation_and_evidence_do_not_repeat_search_terms():
    request = build_lead_search_request("req-2", "  confidential niche  ", "Barcelona")

    assert "confidential niche" not in request.evidence[0].detail
    with pytest.raises(ValueError, match="limit"):
        build_lead_search_request("req-2", "law firms", limit=True)


def test_search_result_rejects_non_mapping_lead():
    with pytest.raises(ValueError, match="lead must be a mapping"):
        search_result_to_opportunities({"leads": [None]})
