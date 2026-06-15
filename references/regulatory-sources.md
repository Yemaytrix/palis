# Palis — Regulatory Source Reference List

These are the **primary, public** regulatory sources Palis grounds against. They serve two purposes:
1. The citable basis for every control in `mcp_server/control_library.py`.
2. The source corpus loaded into the **Foundry IQ** knowledge base, so every finding Palis reports returns a grounded, cited snippet (never an ungrounded assertion).

> All sources below are public regulation text or official government guidance. No paywalled or proprietary content is included in the knowledge base.

---

## United States — FDA / 21 CFR Part 11 (clinical research electronic records)

1. **21 CFR Part 11 — Electronic Records; Electronic Signatures** (the regulation itself)
   - eCFR (always-current): https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11
   - Key sections used: §11.10(a) validation, §11.10(d) limiting system access to authorized individuals, §11.10(e) secure, computer-generated, time-stamped audit trails, §11.50 signature manifestations, §11.100 electronic signature uniqueness.

2. **FDA Final Guidance — "Electronic Systems, Electronic Records, and Electronic Signatures in Clinical Investigations: Questions and Answers"** (October 2024, Final; Docket FDA-2017-D-1105)
   - Primary: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/electronic-systems-electronic-records-and-electronic-signatures-clinical-investigations-questions
   - Federal Register notice: https://www.federalregister.gov/documents/2024/10/02/2024-22562/electronic-systems-electronic-records-and-electronic-signatures-in-clinical-investigations-questions
   - Why it matters: FDA's current thinking on Part 11 for clinical investigations — explicitly names access control, authorized-personnel records, and audit-trail requirements (date/time/user/reason for each record change). This is the control language Palis translates into.

3. **FDA Guidance — "Part 11, Electronic Records; Electronic Signatures — Scope and Application"** (August 2003) — establishes FDA's risk-based interpretation of Part 11.
   - Primary: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application

4. **FDA Draft Guidance — "Considerations for the Use of Artificial Intelligence to Support Regulatory Decision-Making for Drug and Biological Products"** (January 2025) — FDA's first AI-specific guidance; 7-step credibility-assessment framework keyed to the AI's *context of use* and *model risk*.
   - Search/landing: https://www.fda.gov/regulatory-information/search-fda-guidance-documents
   - (Verify the exact deep link in the FDA guidance database before pinning it in the README — the search-documents landing page is the stable entry point.)

5. **FDA Final Guidance — Computer Software Assurance (CSA) for Production and Quality System Software** (September 2025) — modern risk-based software validation approach.
   - Search/landing: https://www.fda.gov/regulatory-information/search-fda-guidance-documents

---

## United States — HHS / HIPAA (PHI handling)

6. **HIPAA Security Rule — 45 CFR Part 164, Subpart C**
   - eCFR: https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C
   - Key sections used: §164.312(a)(1) access control, §164.312(b) audit controls, §164.312(c) integrity.

7. **HIPAA Privacy Rule — Minimum Necessary Standard — 45 CFR §164.502(b)**
   - eCFR: https://www.ecfr.gov/current/title-45/section-164.502
   - HHS overview: https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/minimum-necessary-requirement/index.html

---

## International — clinical research & AI governance

8. **ICH E6(R3) — Good Clinical Practice (GCP)** — delegation of duties, qualified personnel, data integrity. Public via ICH.
   - https://www.ich.org/page/efficacy-guidelines
   - Used for: delegation-of-authority / qualified-personnel reasoning (a study task may only be performed by an appropriately qualified, delegated individual).

9. **FDA–EMA — "Guiding Principles of Good AI Practice in Drug Development"** (January 2026, joint) — current AI-in-drug-development principles.
   - EMA: https://www.ema.europa.eu/en (locate the January 2026 joint principles; confirm deep link before pinning).

10. **NIST AI Risk Management Framework (AI RMF 1.0)** — Govern / Map / Measure / Manage functions.
    - https://www.nist.gov/itl/ai-risk-management-framework

11. **EU GDPR — Article 9 (special categories of personal data, incl. health data)**
    - https://eur-lex.europa.eu/eli/reg/2016/679/oj
    - (EU GMP Annex 22 on AI is *proposed*; cite as forward-looking, not in force.)

---

## Microsoft platform references (for the README architecture section)

- Microsoft Purview DSPM for AI: https://learn.microsoft.com/en-us/purview/dspm-for-ai
- Copilot Control System — Security & Governance: https://learn.microsoft.com/en-us/copilot/microsoft-365/copilot-control-system/security-governance
- Register MCP servers as agent connectors: https://learn.microsoft.com/en-us/microsoftteams/platform/m365-apps/agent-connectors
- Build declarative agents with MCP: https://devblogs.microsoft.com/microsoft365dev/build-declarative-agents-for-microsoft-365-copilot-with-mcp/
- Plugins for Microsoft 365 Copilot: https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/overview-plugins

---

## Positioning note (use in README, honestly)

Palis **complements** Microsoft Purview DSPM for AI and Agent 365 — it does not replace them. Purview/Agent 365 surface generic data-security posture (oversharing, sensitivity labels, audit logs). Palis **translates** that posture into control-by-control, regulator-language attestation for clinical research (21 CFR Part 11, ICH-GCP, HIPAA minimum-necessary), grounded in the sources above. It is a **decision-support and evidence-preparation tool**, not a system of record and not a validated compliance system.
