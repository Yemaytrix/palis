"""
control_library.py
-------------------
The TRANSLATION layer — the part incumbents (Purview DSPM, Zenity, Agent 365)
do NOT do. They surface generic posture ("overshared site", "sensitivity label").
Palis maps each raw finding to a SPECIFIC, NAMED regulatory control and the exact
citation an FDA inspector or IRB uses.

Each control carries a `citation_anchor`: the phrase used to retrieve grounded
source text from the Foundry IQ knowledge base (see references/regulatory-sources.md).
RULE: Palis never reports a gap without a control + a grounded citation. This is
both the differentiator (Creativity & Originality) and the safety mechanism
(Reliability & Safety) — no ungrounded regulatory assertions.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Control:
    id: str                 # internal control id
    framework: str          # e.g. "21 CFR Part 11", "HIPAA Security Rule"
    citation: str           # the exact section a regulator cites
    title: str              # short human-readable control name
    requirement: str        # plain-language statement of what the control requires
    citation_anchor: str    # retrieval key into the Foundry IQ KB for grounded text
    source_url: str         # primary public source (see regulatory-sources.md)


# --- The control catalog (focused on the controls our synthetic gaps exercise) ---
CONTROLS = {
    "P11_AUDIT_TRAIL": Control(
        id="P11_AUDIT_TRAIL",
        framework="21 CFR Part 11",
        citation="21 CFR 11.10(e)",
        title="Secure, computer-generated, time-stamped audit trails",
        requirement=(
            "Use secure, computer-generated, time-stamped audit trails to independently "
            "record the date and time of operator entries and actions that create, modify, "
            "or delete electronic records."
        ),
        citation_anchor="11.10(e) audit trail date time operator create modify delete",
        source_url="https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11",
    ),
    "P11_ACCESS_LIMIT": Control(
        id="P11_ACCESS_LIMIT",
        framework="21 CFR Part 11",
        citation="21 CFR 11.10(d)",
        title="Limiting system access to authorized individuals",
        requirement="Limit system access to authorized individuals.",
        citation_anchor="11.10(d) limiting system access authorized individuals",
        source_url="https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11",
    ),
    "P11_ESIGN": Control(
        id="P11_ESIGN",
        framework="21 CFR Part 11",
        citation="21 CFR 11.50 / 11.100",
        title="Signature manifestation and uniqueness",
        requirement=(
            "Signed electronic records must contain information associated with the signing, "
            "and each electronic signature must be unique to one individual."
        ),
        citation_anchor="11.50 11.100 electronic signature manifestation unique individual",
        source_url="https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11",
    ),
    "HIPAA_MIN_NECESSARY": Control(
        id="HIPAA_MIN_NECESSARY",
        framework="HIPAA Privacy Rule",
        citation="45 CFR 164.502(b)",
        title="Minimum necessary standard",
        requirement=(
            "Limit uses, disclosures, and requests of protected health information to the "
            "minimum necessary to accomplish the intended purpose."
        ),
        citation_anchor="164.502(b) minimum necessary protected health information",
        source_url="https://www.ecfr.gov/current/title-45/section-164.502",
    ),
    "HIPAA_ACCESS_CONTROL": Control(
        id="HIPAA_ACCESS_CONTROL",
        framework="HIPAA Security Rule",
        citation="45 CFR 164.312(a)(1)",
        title="Access control",
        requirement=(
            "Implement technical policies and procedures that allow access to ePHI only to "
            "persons or software programs granted access rights."
        ),
        citation_anchor="164.312(a) access control technical policies ePHI",
        source_url="https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C",
    ),
    "HIPAA_AUDIT_CONTROLS": Control(
        id="HIPAA_AUDIT_CONTROLS",
        framework="HIPAA Security Rule",
        citation="45 CFR 164.312(b)",
        title="Audit controls",
        requirement=(
            "Implement hardware, software, and/or procedural mechanisms that record and "
            "examine activity in information systems that contain or use ePHI."
        ),
        citation_anchor="164.312(b) audit controls record examine activity ePHI",
        source_url="https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C",
    ),
    "GDPR_ART9": Control(
        id="GDPR_ART9",
        framework="EU GDPR",
        citation="GDPR Article 9",
        title="Special categories of personal data (health)",
        requirement=(
            "Processing of health data is prohibited unless a specific Article 9 condition "
            "applies; re-identifiable data is not de-identified data."
        ),
        citation_anchor="Article 9 special categories health data processing",
        source_url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    ),
    "GCP_DELEGATION": Control(
        id="GCP_DELEGATION",
        framework="ICH E6(R3) GCP",
        citation="ICH E6(R3)",
        title="Qualified, delegated personnel & data integrity",
        requirement=(
            "Study tasks may be performed only by appropriately qualified individuals to whom "
            "the task has been delegated; records must be attributable and accurate."
        ),
        citation_anchor="delegation qualified personnel attributable accurate data integrity",
        source_url="https://www.ich.org/page/efficacy-guidelines",
    ),
}


def get_control(control_id: str) -> Control:
    """Return a control definition by id (raises KeyError if unknown — fail loud)."""
    return CONTROLS[control_id]
