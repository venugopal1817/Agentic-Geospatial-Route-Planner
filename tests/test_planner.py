from app.services.planner import build_plan


def test_build_plan_matches_known_village_and_reports_unknown():
    result = build_plan(["Amaravathinagar", "Unknown Village"])

    assert result["total_requested"] == 2
    assert result["total_matched"] == 1
    assert result["matched_villages"][0]["name"] == "Amaravathinagar"
    assert result["unresolved_villages"] == ["Unknown Village"]


def test_build_plan_suggests_close_match_for_misspelled_village():
    result = build_plan(["Guddur"])

    assert result["total_matched"] == 0
    assert result["total_suggested"] == 3
    assert result["suggested_villages"][0]["suggested_match"] == "Gudur"
    assert result["suggested_villages"][0]["status"] == "suggested"
    assert all(sv["score"] >= 0.5 for sv in result["suggested_villages"])


def test_build_plan_returns_all_balapur_variants():
    result = build_plan(["balapur"])

    assert result["total_matched"] == 2
    assert any(match["district"] == "Adilabad" for match in result["matched_villages"])
    assert any(match["district"] == "Ranga Reddy" for match in result["matched_villages"])
