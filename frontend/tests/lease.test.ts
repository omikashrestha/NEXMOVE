import test from "node:test";
import assert from "node:assert/strict";
import { normalizeFlaggedClause, groupFlaggedClauses } from "../lib/lease.ts";

test("Scenario 1: One HIGH-risk clause with backend naming convention", () => {
  const raw = {
    clause_title: "Strict Pet Prohibition",
    raw_text: "No pets allowed on premises under penalty of termination.",
    risk_level: "HIGH",
    advisory_note: "Strict ban on pets with forfeiture clause.",
    suggested_action: "Request a pet addendum.",
    why_it_matters: "Breach leads to total deposit forfeiture."
  };

  const normalized = normalizeFlaggedClause(raw);
  assert.equal(normalized.risk_level, "HIGH");
  assert.equal(normalized.clause_title, "Strict Pet Prohibition");
  assert.equal(normalized.advisory_note, "Strict ban on pets with forfeiture clause.");
  assert.equal(normalized.raw_text, "No pets allowed on premises under penalty of termination.");
  assert.equal(normalized.suggested_action, "Request a pet addendum.");
  assert.equal(normalized.why_it_matters, "Breach leads to total deposit forfeiture.");

  const grouped = groupFlaggedClauses([raw]);
  assert.equal(grouped.needsAttention.length, 1);
  assert.equal(grouped.worthChecking.length, 0);
  assert.equal(grouped.informational.length, 0);
  assert.equal(grouped.totalCount, 1);
  assert.equal(grouped.needsAttention[0].clause_title, "Strict Pet Prohibition");
});

test("Scenario 2: One MEDIUM-risk clause with backend naming convention", () => {
  const raw = {
    clause_title: "Elevator Loading Window",
    raw_text: "Freight movement allowed 10:00 AM to 4:00 PM only.",
    risk_level: "MEDIUM",
    advisory_note: "Heavy shifting must align with society hours.",
    suggested_action: "Ask society management for arrival day permit."
  };

  const normalized = normalizeFlaggedClause(raw);
  assert.equal(normalized.risk_level, "MEDIUM");
  assert.equal(normalized.clause_title, "Elevator Loading Window");
  assert.equal(normalized.advisory_note, "Heavy shifting must align with society hours.");

  const grouped = groupFlaggedClauses([raw]);
  assert.equal(grouped.needsAttention.length, 0);
  assert.equal(grouped.worthChecking.length, 1);
  assert.equal(grouped.informational.length, 0);
  assert.equal(grouped.totalCount, 1);
});

test("Scenario 3: One LOW-risk clause with backend naming convention", () => {
  const raw = {
    clause_title: "Standard Notice Period",
    raw_text: "Either party may terminate with 30 days written notice.",
    risk_level: "LOW",
    advisory_note: "Standard residential notice period."
  };

  const normalized = normalizeFlaggedClause(raw);
  assert.equal(normalized.risk_level, "LOW");
  assert.equal(normalized.clause_title, "Standard Notice Period");
  assert.equal(normalized.advisory_note, "Standard residential notice period.");

  const grouped = groupFlaggedClauses([raw]);
  assert.equal(grouped.needsAttention.length, 0);
  assert.equal(grouped.worthChecking.length, 0);
  assert.equal(grouped.informational.length, 1);
  assert.equal(grouped.totalCount, 1);
});

test("Scenario 4: Correct display and extraction of advisory notes", () => {
  const clauseWithAdvisory = {
    clause_title: "Painting Deduction",
    risk_level: "HIGH",
    advisory_note: "Mandatory non-refundable deduction of one month rent."
  };
  const normalized = normalizeFlaggedClause(clauseWithAdvisory);
  assert.equal(normalized.advisory_note, "Mandatory non-refundable deduction of one month rent.");
});

test("Scenario 5: Missing advisory text provides safe, non-blank fallbacks", () => {
  const highWithoutAdvisory = {
    clause_title: "Security Deposit Forfeiture",
    risk_level: "HIGH",
    advisory_note: "" // missing/empty
  };
  const mediumWithoutAdvisory = {
    clause_title: "Late Fee",
    risk_level: "MEDIUM",
    advisory_note: null
  };
  const lowWithoutAdvisory = {
    clause_title: "Standard Inspection",
    risk_level: "LOW"
  };

  const normHigh = normalizeFlaggedClause(highWithoutAdvisory);
  assert.ok(normHigh.advisory_note.length > 0);
  assert.match(normHigh.advisory_note, /High-risk term/i);

  const normMed = normalizeFlaggedClause(mediumWithoutAdvisory);
  assert.ok(normMed.advisory_note.length > 0);
  assert.match(normMed.advisory_note, /reviewing with your landlord/i);

  const normLow = normalizeFlaggedClause(lowWithoutAdvisory);
  assert.ok(normLow.advisory_note.length > 0);
  assert.match(normLow.advisory_note, /Standard informational/i);
});

test("Scenario 6: Empty, null, or undefined clause lists handled safely", () => {
  const emptyRes = groupFlaggedClauses([]);
  assert.equal(emptyRes.needsAttention.length, 0);
  assert.equal(emptyRes.worthChecking.length, 0);
  assert.equal(emptyRes.informational.length, 0);
  assert.equal(emptyRes.totalCount, 0);

  const nullRes = groupFlaggedClauses(null);
  assert.equal(nullRes.totalCount, 0);

  const undefinedRes = groupFlaggedClauses(undefined);
  assert.equal(undefinedRes.totalCount, 0);

  const nonArrayRes = groupFlaggedClauses({ foo: "bar" });
  assert.equal(nonArrayRes.totalCount, 0);
});

test("Scenario 7: Full compatibility with legacy naming convention (severity, issue_rationale, clause_text)", () => {
  const legacyClauses = [
    {
      clause: "Lock-in forfeiture penalty",
      clause_text: "Early exit prior to 6 months forfeits entire deposit.",
      severity: "HIGH",
      issue_rationale: "Exiting early forfeits entire deposit even with advance notice."
    },
    {
      clause: "Maintenance charge ambiguity",
      clause_text: "Society maintenance billed separately as assessed.",
      severity: "MEDIUM",
      issue_rationale: "Maintenance charges can fluctuate."
    },
    {
      clause: "Annual rent escalation",
      clause_text: "Rent escalates by 5% upon renewal.",
      severity: "LOW",
      issue_rationale: "Standard renewal escalation."
    }
  ];

  const grouped = groupFlaggedClauses(legacyClauses);
  assert.equal(grouped.needsAttention.length, 1);
  assert.equal(grouped.worthChecking.length, 1);
  assert.equal(grouped.informational.length, 1);
  assert.equal(grouped.totalCount, 3);

  // Check HIGH
  assert.equal(grouped.needsAttention[0].risk_level, "HIGH");
  assert.equal(grouped.needsAttention[0].clause_title, "Lock-in forfeiture penalty");
  assert.equal(grouped.needsAttention[0].advisory_note, "Exiting early forfeits entire deposit even with advance notice.");
  assert.equal(grouped.needsAttention[0].raw_text, "Early exit prior to 6 months forfeits entire deposit.");

  // Check MEDIUM
  assert.equal(grouped.worthChecking[0].risk_level, "MEDIUM");
  assert.equal(grouped.worthChecking[0].advisory_note, "Maintenance charges can fluctuate.");

  // Check LOW
  assert.equal(grouped.informational[0].risk_level, "LOW");
  assert.equal(grouped.informational[0].advisory_note, "Standard renewal escalation.");
});

test("Scenario 8: No duplicate clauses across risk sections", () => {
  const mixedClauses = [
    { clause_title: "Clause 1", risk_level: "HIGH", advisory_note: "High 1" },
    { clause_title: "Clause 2", risk_level: "MEDIUM", advisory_note: "Med 1" },
    { clause_title: "Clause 3", risk_level: "LOW", advisory_note: "Low 1" },
    { clause_title: "Clause 4", severity: "HIGH", issue_rationale: "High 2" }
  ];

  const grouped = groupFlaggedClauses(mixedClauses);
  assert.equal(grouped.needsAttention.length, 2);
  assert.equal(grouped.worthChecking.length, 1);
  assert.equal(grouped.informational.length, 1);
  assert.equal(grouped.totalCount, 4);

  const allTitles = [
    ...grouped.needsAttention.map(c => c.clause_title),
    ...grouped.worthChecking.map(c => c.clause_title),
    ...grouped.informational.map(c => c.clause_title)
  ];
  const uniqueTitles = new Set(allTitles);
  assert.equal(allTitles.length, uniqueTitles.size, "No clause should appear in more than one category");
});
