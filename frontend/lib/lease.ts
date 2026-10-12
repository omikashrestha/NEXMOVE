export type LeaseRiskLevel = "HIGH" | "MEDIUM" | "LOW";

export interface FlaggedClauseItem {
  clause_title: string;
  raw_text: string;
  risk_level: LeaseRiskLevel;
  advisory_note: string;
  suggested_action?: string | null;
  why_it_matters?: string | null;
}

export interface GroupedLeaseClauses {
  needsAttention: FlaggedClauseItem[];
  worthChecking: FlaggedClauseItem[];
  informational: FlaggedClauseItem[];
  totalCount: number;
}

/**
 * Normalizes a lease clause from backend payload or legacy structure.
 * Handles both:
 * - Current backend contract: risk_level, advisory_note, raw_text, clause_title, why_it_matters, suggested_action
 * - Legacy contract: severity, issue_rationale, clause_text, clause
 */
export function normalizeFlaggedClause(clause: any): FlaggedClauseItem {
  if (!clause || typeof clause !== "object") {
    return {
      clause_title: "General Lease Term",
      raw_text: "",
      risk_level: "LOW",
      advisory_note: "Review this lease term with your landlord before signing.",
      suggested_action: null,
      why_it_matters: null,
    };
  }

  // 1. Risk level / Severity normalization
  const rawRisk = String(clause.risk_level || clause.severity || "").trim().toUpperCase();
  let risk_level: LeaseRiskLevel = "LOW";
  if (rawRisk === "HIGH" || rawRisk === "CRITICAL") {
    risk_level = "HIGH";
  } else if (rawRisk === "MEDIUM" || rawRisk === "MODERATE") {
    risk_level = "MEDIUM";
  } else {
    risk_level = "LOW";
  }

  // 2. Advisory note / Rationale normalization with helpful non-blank fallbacks
  const rawAdvisory = String(
    clause.advisory_note ||
    clause.issue_rationale ||
    ""
  ).trim();

  let advisory_note = rawAdvisory;
  if (!advisory_note) {
    if (clause.why_it_matters && String(clause.why_it_matters).trim()) {
      advisory_note = String(clause.why_it_matters).trim();
    } else if (risk_level === "HIGH") {
      advisory_note = "High-risk term that may impose financial deductions, deposit forfeiture, or strict move-in restrictions.";
    } else if (risk_level === "MEDIUM") {
      advisory_note = "Clause worth reviewing with your landlord or society management before signing.";
    } else {
      advisory_note = "Standard informational lease condition.";
    }
  }

  // 3. Clause title normalization
  const clause_title = String(
    clause.clause_title ||
    clause.title ||
    clause.clause ||
    (risk_level === "HIGH" ? "Critical Lease Clause" : "Lease Term")
  ).trim();

  // 4. Raw text / Excerpt normalization
  const raw_text = String(clause.raw_text || clause.clause_text || clause.text || "").trim();

  // 5. Why it matters & suggested action
  const why_it_matters = clause.why_it_matters ? String(clause.why_it_matters).trim() : null;
  const suggested_action = clause.suggested_action ? String(clause.suggested_action).trim() : null;

  return {
    clause_title,
    raw_text,
    risk_level,
    advisory_note,
    suggested_action,
    why_it_matters,
  };
}

/**
 * Groups an array of raw or normalized clauses into mutually exclusive buckets:
 * - needsAttention (HIGH risk)
 * - worthChecking (MEDIUM risk)
 * - informational (LOW risk)
 *
 * Guarantees no clause is duplicated across sections and safely handles missing or empty arrays.
 */
export function groupFlaggedClauses(rawClauses: any): GroupedLeaseClauses {
  if (!Array.isArray(rawClauses) || rawClauses.length === 0) {
    return {
      needsAttention: [],
      worthChecking: [],
      informational: [],
      totalCount: 0,
    };
  }

  const normalized = rawClauses.map(normalizeFlaggedClause);

  const needsAttention: FlaggedClauseItem[] = [];
  const worthChecking: FlaggedClauseItem[] = [];
  const informational: FlaggedClauseItem[] = [];

  for (const clause of normalized) {
    if (clause.risk_level === "HIGH") {
      needsAttention.push(clause);
    } else if (clause.risk_level === "MEDIUM") {
      worthChecking.push(clause);
    } else {
      informational.push(clause);
    }
  }

  return {
    needsAttention,
    worthChecking,
    informational,
    totalCount: normalized.length,
  };
}
