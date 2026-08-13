from app.services.retrieval import VillageRetrievalService
from app.services.intent_parser import IntentParser


def test_retrieval_exact_match_for_known_village():
    service = VillageRetrievalService()
    result = service.retrieve_candidates("Balapur")
    assert len(result) >= 1
    assert any("Balapur" in row.get("village", "") for row in result)


def test_retrieval_ambiguous_candidate_returns_multiple_records():
    service = VillageRetrievalService()
    result = service.retrieve_candidates("Balapur")
    assert len(result) >= 2


def test_intent_parser_extracts_origin_and_destinations():
    parsed = IntentParser.parse("I need to start from Hyderabad and visit Balapur, Mallapur and Chintapalli.")
    assert parsed.origin == "Hyderabad"
    assert "Balapur" in parsed.destinations
    assert "Mallapur" in parsed.destinations
    assert "Chintapalli" in parsed.destinations


def test_parse_rejects_empty_text():
    try:
        IntentParser.parse("")
        assert False, "Expected ValueError for empty text"
    except ValueError:
        pass
