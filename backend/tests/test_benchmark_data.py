import json
from pathlib import Path
from backend.app.core.config import DATA_DIR
from backend.app.schemas.housing import HousingProposal


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
