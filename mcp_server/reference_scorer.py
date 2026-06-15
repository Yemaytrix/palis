"""
reference_scorer.py
-------------------
>>> IP FIREWALL <<<
This is a SIMPLIFIED, TRANSPARENT REFERENCE IMPLEMENTATION of the Palis posture
score, provided so the public hackathon repo is fully runnable and auditable.

The PRODUCTION scoring methodology (dimension weighting, calibration, and the
Effective-posture index) is PROPRIETARY and is NOT contained in this repository.
A reviewer can read this file end-to-end and understand exactly how the demo
score is produced — by design. Nothing here exposes the commercial method.

Design choices and why:
- Rule-based, not ML: a compliance score must be explainable and repeatable.
  An auditor needs to know *why* a number is what it is. Deterministic rules make
  every score defensible (Reasoning & Multi-step Thinking; Reliability & Safety).
- Five dimensions, each 0-100, then a transparent weighted composite.
- Output is a band (RED/AMBER/GREEN) plus per-dimension detail and the list of
  triggered control gaps (control ids resolved against control_library.py).
"""

from dataclasses import dataclass, field


# Dimensions deliberately mirror what regulators actually examine.
DIMENSIONS = [
    "data_classification_coverage",   # can controls even be enforced/proven?
    "access_appropriateness",         # minimum necessary / least privilege
    "audit_trail_integrity",          # Part 11 11.10(e), HIPAA 164.312(b)
    "exposure_risk",                   # PHI + broad access + unlabeled = exposure
    "regulatory_alignment",           # aggregate alignment signal
]

# Transparent, published weights. Production weights are proprietary (see header).
WEIGHTS = {
    "data_classification_coverage": 0.20,
    "access_appropriateness": 0.25,
    "audit_trail_integrity": 0.25,
    "exposure_risk": 0.20,
    "regulatory_alignment": 0.10,
}


@dataclass
class Finding:
    """A single triggered gap: which dimension, which control, why."""
    dimension: str
    control_id: str          # resolves against control_library.CONTROLS
    severity: str            # "high" | "medium"
    rationale: str           # plain-language, evidence-based reason


@dataclass
class ScoreResult:
    agent_id: str
    composite: int
    band: str                                  # RED | AMBER | GREEN
    dimensions: dict = field(default_factory=dict)  # dim -> 0..100
    findings: list = field(default_factory=list)    # list[Finding]


def _has_phi(agent: dict) -> bool:
    return any(s.get("contains_phi") for s in agent["data_sources"])


def _any_unlabeled(agent: dict) -> bool:
    return any(s.get("classification") == "unlabeled" for s in agent["data_sources"])


def _any_reidentifiable(agent: dict) -> bool:
    return any(s.get("reidentifiable") for s in agent["data_sources"])


def score_agent(agent: dict) -> ScoreResult:
    """
    Evaluate one agent's governance posture against the regulated-data rules.
    Each rule below ties a concrete data condition to a named control gap, so the
    score is never a black box — it is a chain of explainable rules.
    """
    dims = {d: 100 for d in DIMENSIONS}   # start at full marks, deduct on gaps
    findings: list[Finding] = []
    phi = _has_phi(agent)
    controls = agent["controls"]
    access = agent["access"]

    # If the agent touches no regulated data, regulated-data rules don't apply.
    if not phi:
        return ScoreResult(
            agent_id=agent["id"], composite=100, band="GREEN",
            dimensions=dims, findings=[],
        )

    # Rule 1 — Data classification coverage. Unlabeled PHI source => controls
    # cannot be enforced or *proven*, which is itself the gap.
    if _any_unlabeled(agent):
        dims["data_classification_coverage"] = 30
        dims["exposure_risk"] -= 40
        findings.append(Finding(
            dimension="data_classification_coverage",
            control_id="HIPAA_ACCESS_CONTROL",
            severity="high",
            rationale="A PHI-bearing source is unclassified; data-handling controls "
                      "cannot be applied or demonstrated to a reviewer.",
        ))

    # Rule 2 — Access appropriateness (minimum necessary / least privilege).
    # PHI + broad audience => HIPAA minimum-necessary + access-control gap.
    if phi and access.get("audience") == "all_staff":
        dims["access_appropriateness"] = 20
        dims["exposure_risk"] -= 40
        findings.append(Finding(
            dimension="access_appropriateness",
            control_id="HIPAA_MIN_NECESSARY",
            severity="high",
            rationale="PHI source is reachable by all staff, exceeding the minimum "
                      "necessary for the agent's purpose.",
        ))

    # Rule 3 — Audit-trail integrity. Regulated/study record changes without a
    # secure, time-stamped audit trail => Part 11 11.10(e) + HIPAA 164.312(b).
    if phi and not controls.get("audit_trail"):
        dims["audit_trail_integrity"] = 15
        findings.append(Finding(
            dimension="audit_trail_integrity",
            control_id="P11_AUDIT_TRAIL",
            severity="high",
            rationale="No secure, computer-generated, time-stamped audit trail of "
                      "record create/modify/delete actions.",
        ))

    # Rule 4 — Re-identifiable data treated as de-identified.
    if _any_reidentifiable(agent) and not controls.get("deidentification"):
        dims["regulatory_alignment"] -= 50
        dims["exposure_risk"] -= 20
        findings.append(Finding(
            dimension="regulatory_alignment",
            control_id="GDPR_ART9",
            severity="high",
            rationale="A re-identifiable source is used without a de-identification "
                      "control; re-identifiable data is not de-identified.",
        ))

    # Rule 5 — Study records that may bear signatures without an e-signature control.
    if agent.get("study") and not controls.get("esignature"):
        dims["regulatory_alignment"] -= 15
        findings.append(Finding(
            dimension="regulatory_alignment",
            control_id="P11_ESIGN",
            severity="medium",
            rationale="Study-related records may require signature manifestation; no "
                      "e-signature control is configured.",
        ))

    # Clamp dimensions to [0, 100].
    for d in dims:
        dims[d] = max(0, min(100, dims[d]))

    # Transparent weighted composite of the dimensions.
    composite = round(sum(dims[d] * WEIGHTS[d] for d in DIMENSIONS))

    # Severity ceiling — a core compliance principle: a single CRITICAL control
    # failure caps the overall posture grade regardless of how strong the other
    # dimensions are. You cannot average away a hard failure, and a regulator
    # won't either. This also keeps the displayed number coherent with the band
    # (no "90 but RED"). Ceilings: high -> 55 (RED), medium -> 78 (AMBER).
    has_high = any(f.severity == "high" for f in findings)
    has_medium = any(f.severity == "medium" for f in findings)
    if has_high:
        composite = min(composite, 55)
        band = "RED"
    elif has_medium:
        composite = min(composite, 78)
        band = "AMBER"
    elif composite < 80:
        band = "AMBER"
    else:
        band = "GREEN"

    return ScoreResult(
        agent_id=agent["id"], composite=composite, band=band,
        dimensions=dims, findings=findings,
    )
