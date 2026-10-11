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
        filename = "sample_lease_agreement.txt"
        is_sample = True

        if file_path and file_path.exists():
            filename = file_path.name
            text = file_path.read_text(encoding="utf-8")
            is_sample = "sample" in str(file_path).lower() or "lease_" in filename
        elif raw_text_content is not None:
            text = raw_text_content
            is_sample = False
        else:
            text = None

        if not text or not text.strip():
            return DocumentAudit(
                document_filename=filename,
                parse_status="FAILED",
                disclaimer="Automated extraction for informational user review only. Does not constitute formal legal counsel or advice.",
                is_sample_document=True
            )

        # 1. Financial Extractions via pattern matching
        # Rent match: Look specifically for rent clause or first prominent rupee figure
        rent_match = re.search(r"(?:rent\s*of|base\s*rent\s*of|monthly\s*rent.*?)\s*₹\s*([0-9]{2,3},[0-9]{3}|[0-9]{4,6})", text, re.IGNORECASE)
        if not rent_match:
            rent_match = re.search(r"₹\s*([0-9]{2,3},[0-9]{3}|[0-9]{4,6})", text)
        
        extracted_rent = None
        if rent_match:
            try:
                extracted_rent = float(rent_match.group(1).replace(",", ""))
            except ValueError:
                pass

        deposit_match = re.search(r"security\s*deposit.*?₹\s*([0-9]{2,3},[0-9]{3}|[0-9]{4,6})", text, re.IGNORECASE)
        extracted_deposit = None
        if deposit_match:
            try:
                extracted_deposit = float(deposit_match.group(1).replace(",", ""))
            except ValueError:
                pass

        maint_match = re.search(r"(?:society\s*maintenance|maintenance\s*charge).*?₹\s*([0-9]{1,3},[0-9]{3}|[0-9]{3,5})", text, re.IGNORECASE)
        extracted_maint = None
        if maint_match:
            try:
                extracted_maint = float(maint_match.group(1).replace(",", ""))
            except ValueError:
                pass

        notice_match = re.search(r"([0-9]+)\s*(?:\([a-zA-Z]+\))?\s*month[s]?\s*(?:written)?\s*notice", text, re.IGNORECASE)
        notice_days = int(notice_match.group(1)) * 30 if notice_match else 30

        lockin_match = re.search(r"lock-in\s*period\s*(?:of)?\s*([0-9]+)\s*month", text, re.IGNORECASE)
        lockin_months = int(lockin_match.group(1)) if lockin_match else None

        # 2. Risk Clause Flagging
        flagged: List[FlaggedClause] = []

        # Check for missing critical financial terms
        is_missing_terms = False
        if extracted_rent is None or extracted_deposit is None:
            is_missing_terms = True
            flagged.append(FlaggedClause(
                clause_title="Missing Key Financial Terms",
                raw_text="The agreement is missing explicit monthly rent or security deposit amounts.",
                risk_level="HIGH",
                advisory_note="Key financial commitments are absent or ambiguous in the provided text.",
                suggested_action="Request an updated draft with all rent, deposit, and refund terms explicitly defined in writing.",
                why_it_matters="Signing without written amounts leaves you vulnerable to arbitrary fee demands."
            ))

        # Check for mandatory repainting / deductions
        if re.search(r"deduct.*?(?:painting|repainting|refurbish)", text, re.IGNORECASE):
            is_high_cost = bool(re.search(r"1\s*(?:\([a-zA-Z]+\))?\s*full\s*month", text, re.IGNORECASE))
            flagged.append(FlaggedClause(
                clause_title="Mandatory Painting / Exit Deduction",
                raw_text="Clause stipulates non-refundable repaint or sanitization deduction from security deposit upon vacating.",
                risk_level="HIGH" if is_high_cost else "MEDIUM",
                advisory_note="Landlord deducts non-refundable sum for painting regardless of tenancy duration or wall condition.",
                suggested_action='Ask the landlord: "Can we add wording that deductions only apply to physical damage beyond normal wear and tear?"',
                why_it_matters="You may forfeit a substantial portion of your deposit even if the property is kept immaculate."
            ))

        # Check for strict pet bans
        if re.search(r"no pets|strict pet restriction|forfeiture of.*deposit.*pet|no pets of any species", text, re.IGNORECASE):
            flagged.append(FlaggedClause(
                clause_title="Strict Pet Prohibition & Forfeiture Risk",
                raw_text="No pets allowed on premises; breach carries penalty of immediate lease termination or deposit forfeiture.",
                risk_level="HIGH",
                advisory_note="Strict prohibition against companion animals. Breach triggers immediate lease termination.",
                suggested_action='Ask the landlord: "Can a pet addendum be executed granting permission for our domestic pet?"',
                why_it_matters="Keeping a pet will trigger immediate lease cancellation and total deposit loss."
            ))

        # Check for lock-in early termination forfeiture
        if re.search(r"prior to.*?lock-in.*?forfeited|prior to 6 months.*?forfeited|deposit shall be forfeited", text, re.IGNORECASE):
            flagged.append(FlaggedClause(
                clause_title="Early Exit Deposit Forfeiture",
                raw_text="Vacating prior to lock-in period results in total forfeiture of security deposit.",
                risk_level="HIGH",
                advisory_note="Exiting early forfeits your entire deposit even with advance notice.",
                suggested_action='Ask the landlord: "Can early termination be permitted with standard 2-month notice in case of emergency or job relocation?"',
                why_it_matters="If your employer reassigns you or personal circumstances change, you cannot exit without total financial penalty."
            ))

        # Check for moving / elevator time restrictions
        if re.search(r"elevator.*hours|move-in.*hours|loading.*?restricted|freight movement", text, re.IGNORECASE):
            time_match = re.search(r"([0-9]{1,2}:[0-9]{2}\s*[AP]M\s*to\s*[0-9]{1,2}:[0-9]{2}\s*[AP]M)", text, re.IGNORECASE)
            hours_str = time_match.group(1) if time_match else "Restricted weekday window"
            flagged.append(FlaggedClause(
                clause_title="Restricted Move-In / Elevator Access Hours",
                raw_text=f"Heavy luggage shifting and moving van unloading restricted to: {hours_str}.",
                risk_level="MEDIUM",
                advisory_note="Packers and movers delivery schedule must be coordinated strictly within this designated window.",
                suggested_action='Ask society management: "Can we request a weekend permit or elevator access window for arrival day?"',
                why_it_matters="Your movers may be barred entry if they arrive outside this narrow window, causing unloading delays."
            ))

        # Check for late payment penalties
        if re.search(r"late payment.*?charge.*?per day|delay.*?₹\s*500", text, re.IGNORECASE):
            flagged.append(FlaggedClause(
                clause_title="Daily Late Payment Penalties",
                raw_text="A daily penalty fee applies immediately after rent due date.",
                risk_level="MEDIUM",
                advisory_note="Daily compounding late fee applies without a grace period.",
                suggested_action='Ask the landlord: "Can we add a 5-day grace period for electronic bank transfers?"',
                why_it_matters="Bank holidays or payroll processing delays could incur compounding penalties."
            ))

        parse_status = "NEEDS_MANUAL_REVIEW" if is_missing_terms else "SUCCESS"

        return DocumentAudit(
            document_filename=filename,
            parse_status=parse_status,
            extracted_monthly_rent_inr=extracted_rent,
            extracted_security_deposit_inr=extracted_deposit,
            extracted_notice_period_days=notice_days,
            extracted_lock_in_months=lockin_months,
            extracted_maintenance_inr=extracted_maint,
            flagged_clauses_for_review=flagged,
            disclaimer="Automated extraction for informational user review only. Does not constitute formal legal counsel or legal advice.",
            is_sample_document=is_sample
        )
