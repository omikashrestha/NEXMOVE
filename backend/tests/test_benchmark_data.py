import json
import tempfile
from pathlib import Path
import pytest

from backend.app.core.config import DATA_DIR
from backend.app.schemas.housing import HousingProposal
from backend.app.schemas.state import RelocationProfile
from backend.app.schemas.arbitration import RevisionRequest
from backend.app.agents.housing import HousingResearchAgent
from backend.app.agents.document import DocumentIntelligenceAgent


def test_housing_samples_json_integrity():
    housing_file = DATA_DIR / "housing_samples_inr.json"
    assert housing_file.exists(), f"Missing housing sample dataset at {housing_file}"

    with open(housing_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert data["metadata"]["currency"] == "INR"
    assert "SYNTHETIC_BENCHMARK" in data["metadata"]["dataset_type"]
    assert "listings" in data
    assert len(data["listings"]) >= 20

    for item in data["listings"]:
        assert item["monthly_rent_inr"] > 0
        assert item["security_deposit_inr"] >= 0
        assert item["bhk"] in [1, 2, 3]
        assert isinstance(item["pet_friendly"], bool)
        assert 1.0 <= item["safety_score_index"] <= 10.0

        # Verify mapping into HousingProposal schema
        proposal = HousingProposal(
            property_id=item["property_id"],
            title=item["title"],
            city=item["city"],
            neighborhood=item["neighborhood"],
            bhk=item["bhk"],
            monthly_rent_inr=item["monthly_rent_inr"],
            security_deposit_inr=item["security_deposit_inr"],
            society_maintenance_inr=item["society_maintenance_inr"],
            move_in_fee_inr=item["move_in_fee_inr"],
            pet_friendly=item["pet_friendly"],
            commute_to_workplace_mins=item["commute_to_manyata_mins"],
            safety_score_index=item["safety_score_index"]
        )
        assert proposal.property_id == item["property_id"]


def test_logistics_tariffs_json_integrity():
    tariff_file = DATA_DIR / "logistics_tariffs_inr.json"
    assert tariff_file.exists(), f"Missing logistics tariff dataset at {tariff_file}"

    with open(tariff_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert data["metadata"]["currency"] == "INR"
    assert "corridors" in data
    assert len(data["corridors"]) >= 4

    # Specifically check the Pune -> Bengaluru corridor
    pun_blr = next((c for c in data["corridors"] if c["corridor_id"] == "PUN-BLR"), None)
    assert pun_blr is not None
    assert pun_blr["distance_km"] == 840
    assert pun_blr["standard_transit_days"] == 3
    assert "2" in pun_blr["bhk_tariffs"]
    assert pun_blr["bhk_tariffs"]["2"]["base_packers_movers_quote_inr"] == 38000.0


def test_sample_leases_text_files():
    leases_dir = DATA_DIR / "sample_leases"
    assert leases_dir.exists(), f"Missing sample leases directory at {leases_dir}"

    std_lease = leases_dir / "lease_standard_inr.txt"
    redflag_lease = leases_dir / "lease_redflag_inr.txt"

    assert std_lease.exists()
    assert redflag_lease.exists()

    std_text = std_lease.read_text(encoding="utf-8")
    assert "₹30,000" in std_text
    assert "₹60,000" in std_text
    assert "HSR Layout" in std_text

    rf_text = redflag_lease.read_text(encoding="utf-8")
    assert "MANDATORY REPAINTING DEDUCTION" in rf_text
    assert "STRICT PET RESTRICTION" in rf_text
    assert "₹38,000" in rf_text


def test_housing_agent_pet_restriction_never_ignored_under_extreme_limits():
    """Regression test: pet accommodations are a non-negotiable hard constraint under budget pressure."""
    profile = RelocationProfile(
        user_id="usr-bench-pet-regr",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=150000.0,
        monthly_budget_limit_inr=40000.0,
        home_bhk=3,
        has_pets=True
    )
    agent = HousingResearchAgent()
    # Force a revision request with rent lower than any 3BHK pet-friendly property
    rev_req = RevisionRequest(
        target_agent="HousingResearchAgent",
        conflict_type="UPFRONT_BUDGET_OVERRUN",
        hard_limits={"max_monthly_rent": 25000.0, "max_security_deposit": 50000.0},
        soft_relaxations={},
        rationale="Severe budget constraint"
    )
    proposal = agent.search(profile, revision_request=rev_req)
    # The selected property MUST remain pet-friendly
    assert proposal.pet_friendly is True
    assert proposal.datasource == "SYNTHETIC_BENCHMARK_INR"


def test_housing_agent_raises_when_synthetic_dataset_has_no_pet_units():
    """Regression test: search raises explicit ValueError if dataset contains no pet accommodations."""
    dataset_no_pets = {
        "metadata": {"currency": "INR", "dataset_type": "SYNTHETIC_BENCHMARK"},
        "listings": [
            {
                "property_id": "NO-PET-01",
                "city": "Bengaluru",
                "neighborhood": "Koramangala",
                "bhk": 2,
                "title": "Strict No Pets Residency",
                "monthly_rent_inr": 28000.0,
                "security_deposit_inr": 56000.0,
                "pet_friendly": False,
                "safety_score_index": 8.0,
                "commute_to_manyata_mins": 30
            }
        ]
    }
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
        json.dump(dataset_no_pets, tmp)
        tmp_path = Path(tmp.name)

    try:
        agent = HousingResearchAgent(data_path=tmp_path)
        pet_profile = RelocationProfile(
            user_id="usr-pet-fail",
            origin_city="Pune",
            destination_city="Bengaluru",
            target_move_date="2026-11-05",
            upfront_budget_limit_inr=150000.0,
            monthly_budget_limit_inr=40000.0,
            home_bhk=2,
            has_pets=True
        )
        with pytest.raises(ValueError, match="No pet-friendly accommodations available"):
            agent.search(pet_profile)
    finally:
        tmp_path.unlink()


def test_housing_agent_handles_missing_housing_fields_gracefully():
    """Regression test: missing or None numerical fields in synthetic listings fallback to safe defaults."""
    sparse_dataset = {
        "metadata": {"currency": "INR", "dataset_type": "SYNTHETIC_BENCHMARK"},
        "listings": [
            {
                "property_id": "SPARSE-BLR-01",
                "city": "Bengaluru",
                "neighborhood": "Hebbal",
                "bhk": 2,
                "title": "Minimal Data 2BHK",
                "monthly_rent_inr": 31000.0,
                "security_deposit_inr": 62000.0,
                "society_maintenance_inr": None,
                "move_in_fee_inr": None,
                "safety_score_index": None,
                "commute_to_manyata_mins": None,
                "pet_friendly": True
            }
        ]
    }
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
        json.dump(sparse_dataset, tmp)
        tmp_path = Path(tmp.name)

    try:
        agent = HousingResearchAgent(data_path=tmp_path)
        profile = RelocationProfile(
            user_id="usr-sparse",
            origin_city="Pune",
            destination_city="Bengaluru",
            target_move_date="2026-11-05",
            upfront_budget_limit_inr=150000.0,
            monthly_budget_limit_inr=40000.0,
            home_bhk=2,
            has_pets=True
        )
        proposal = agent.search(profile)
        assert proposal.property_id == "SPARSE-BLR-01"
        assert proposal.society_maintenance_inr == 0.0
        assert proposal.move_in_fee_inr == 0.0
        assert proposal.safety_score_index == 8.0
        assert proposal.commute_to_workplace_mins == 30
        assert proposal.pet_friendly is True
        assert proposal.datasource == "SYNTHETIC_BENCHMARK_INR"
    finally:
        tmp_path.unlink()


def test_document_agent_risky_clauses_informational_disclaimer():
    """Regression test: all document audits carrying risk clauses retain an informational-only disclaimer."""
    agent = DocumentIntelligenceAgent()
    redflag_path = DATA_DIR / "sample_leases" / "lease_redflag_inr.txt"
    audit = agent.analyze_document(file_path=redflag_path)

    assert audit.parse_status == "SUCCESS"
    assert len(audit.flagged_clauses_for_review) >= 3
    # Check that informational disclaimer is explicitly populated
    assert "informational user review only" in audit.disclaimer.lower()
    assert "does not constitute formal legal counsel" in audit.disclaimer.lower()

    # Empty / whitespace document must also return disclaimer and status FAILED
    empty_audit = agent.analyze_document(raw_text_content="    ")
    assert empty_audit.parse_status == "FAILED"
    assert "does not constitute formal legal counsel" in empty_audit.disclaimer.lower()

