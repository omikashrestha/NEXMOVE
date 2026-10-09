from backend.app.schemas.state import RelocationProfile
from backend.app.schemas.housing import HousingProposal
from backend.app.schemas.logistics import LogisticsEstimate
from backend.app.schemas.budget import (
    OneTimeRelocationCosts,
    InitialHousingOutlay,
    RecurringMonthlyCosts,
    BudgetAudit
)


class BudgetAnalystAgent:
    """Specialized financial intelligence agent auditing three-tier relocation costs in INR."""

    def audit(
        self,
        profile: RelocationProfile,
        housing_proposal: HousingProposal,
        logistics_estimate: LogisticsEstimate
    ) -> BudgetAudit:
        """Audits both upfront capital requirements and monthly operational living costs."""

        # Tier 1: One-Time Relocation Costs
        one_time = OneTimeRelocationCosts(
            packers_movers_inr=logistics_estimate.base_packers_movers_quote_inr + logistics_estimate.vehicle_shipping_inr,
            transit_insurance_inr=logistics_estimate.transit_insurance_inr,
            travel_tickets_inr=5000.0,  # Standard interstate train/flight travel estimate for family
            packing_supplies_inr=2500.0
        )

        # Tier 2: Initial Housing Outlay
        outlay = InitialHousingOutlay(
            security_deposit_inr=housing_proposal.security_deposit_inr,
            advance_rent_inr=housing_proposal.monthly_rent_inr,
            move_in_fee_inr=housing_proposal.move_in_fee_inr
        )

        # Tier 3: Recurring Monthly Living Costs
        # Commute cost estimated at ₹100 per day for 22 working days, scaled by commute duration
        commute_daily = max(50.0, float(housing_proposal.commute_to_workplace_mins) * 3.5)
        monthly_commute = round(commute_daily * 22, 2)

        recurring = RecurringMonthlyCosts(
            monthly_base_rent_inr=housing_proposal.monthly_rent_inr,
            society_maintenance_inr=housing_proposal.society_maintenance_inr,
            estimated_utilities_inr=3500.0,  # Baseline electricity, water, gas, WiFi
            estimated_commute_inr=monthly_commute
        )

        return BudgetAudit(
            one_time_costs=one_time,
            housing_outlay=outlay,
            upfront_budget_limit_inr=profile.upfront_budget_limit_inr,
            recurring_monthly_costs=recurring,
            monthly_budget_limit_inr=profile.monthly_budget_limit_inr
        )
