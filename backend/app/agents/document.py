import re
from pathlib import Path
from typing import Optional, List

from backend.app.schemas.document import FlaggedClause, DocumentAudit


class DocumentIntelligenceAgent:
    """Specialized agent extracting lease clauses and flagging contractual risks for user review."""

    def analyze_document(
        self,
        file_path: Optional[Path] = None,
        raw_text_content: Optional[str] = None
    ) -> DocumentAudit:
        """Parses lease agreement text, extracts financial terms, and flags risk clauses."""
        filename = "provided_lease_document.txt"

        if file_path and file_path.exists():
            filename = file_path.name
            text = file_path.read_text(encoding="utf-8")
        elif raw_text_content:
            text = raw_text_content
        else:
            return DocumentAudit(
                document_filename=filename,
                parse_status="FAILED",
                disclaimer="Automated extraction for informational user review only. Does not constitute formal legal counsel."
            )

        # 1. Financial Extractions via pattern matching
        rent_match = re.search(r"₹\s*([0-9]{2,3},[0-9]{3}|[0-9]{4,6})", text)
        extracted_rent = None
        if rent_match:
            try:
                extracted_rent = float(rent_match.group(1).replace(",", ""))
            except ValueError:
                pass

        deposit_match = re.search(r"security deposit.*?₹\s*([0-9]{2,3},[0-9]{3}|[0-9]{4,6})", text, re.IGNORECASE)
        extracted_deposit = None
        if deposit_match:
            try:
                extracted_deposit = float(deposit_match.group(1).replace(",", ""))
            except ValueError:
                pass

        notice_match = re.search(r"([0-9]+)\s*(?:\([a-zA-Z]+\))?\s*month[s]?\s*(?:written)?\s*notice", text, re.IGNORECASE)
        notice_days = int(notice_match.group(1)) * 30 if notice_match else 30

        lockin_match = re.search(r"lock-in\s*period\s*of\s*([0-9]+)\s*month", text, re.IGNORECASE)
        lockin_months = int(lockin_match.group(1)) if lockin_match else None

        # 2. Risk Clause Flagging
        flagged: List[FlaggedClause] = []

        # Check for mandatory repainting / deductions
        if re.search(r"deduct.*?(?:painting|repainting|refurbish)", text, re.IGNORECASE):
            flagged.append(FlaggedClause(
                clause_title="Mandatory Painting / Exit Deduction",
                raw_text="Clause stipulates non-refundable repaint or sanitization deduction from security deposit upon vacating.",
                risk_level="MEDIUM",
                advisory_note="Common in regional tenancy contracts; budget for this non-refundable loss upon lease termination."
            ))

        # Check for strict pet bans
        if re.search(r"no pets|strict pet restriction|forfeiture of.*deposit.*pet", text, re.IGNORECASE):
            flagged.append(FlaggedClause(
                clause_title="Strict Pet Prohibition & Forfeiture Risk",
                raw_text="No pets allowed on premises; breach carries penalty of immediate lease termination or deposit forfeiture.",
                risk_level="HIGH",
                advisory_note="Violates pet accommodation requirement. Do not sign if household includes companion animals."
            ))

        # Check for moving / elevator time restrictions
        if re.search(r"elevator.*hours|move-in.*hours|loading.*?restricted", text, re.IGNORECASE):
            time_match = re.search(r"([0-9]{1,2}:[0-9]{2}\s*[AP]M\s*to\s*[0-9]{1,2}:[0-9]{2}\s*[AP]M)", text, re.IGNORECASE)
            hours_str = time_match.group(1) if time_match else "Restricted weekday window"
            flagged.append(FlaggedClause(
                clause_title="Restricted Move-In / Elevator Access Hours",
                raw_text=f"Heavy luggage shifting and moving van unloading restricted to: {hours_str}.",
                risk_level="MEDIUM",
                advisory_note="Packers and movers delivery schedule must be coordinated strictly within this designated window."
            ))

        return DocumentAudit(
            document_filename=filename,
            parse_status="SUCCESS",
            extracted_monthly_rent_inr=extracted_rent,
            extracted_security_deposit_inr=extracted_deposit,
            extracted_notice_period_days=notice_days,
            extracted_lock_in_months=lockin_months,
            flagged_clauses_for_review=flagged,
            disclaimer="Automated extraction for informational user review only. Does not constitute formal legal counsel."
        )
