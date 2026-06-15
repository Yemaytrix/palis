# Palis — Project Description

## Problem it solves

In clinical research, the most dangerous compliance failures are not missing documents — they are *timing* failures. A coordinator can perform a regulated task (informed consent, eligibility assessment) before she is actually authorized to: before her name is effective on the study's Delegation of Authority Log, or before the Principal Investigator has signed it. Because every signature eventually lands, the finished log looks valid. The violation lives in the sequence of dates, and it is typically caught only at audit, where it becomes a documented deviation.

A second, newer version of the same problem is now appearing: Microsoft 365 Copilot agents are being deployed into regulated environments where they touch PHI, with no independent check of whether each agent handles that data in line with 21 CFR Part 11, HIPAA, and GDPR.

Existing tools manage the delegation log and the agent registry as *documents and inventories*. None of them answer the operative question: **was this activity actually authorized at the moment it happened, and does it hold up against a cited regulation?**

## What Palis is

Palis is an independent compliance agent for clinical research, delivered as a **Microsoft 365 Copilot declarative agent** backed by an **external MCP server**, with every regulatory citation grounded live in **Microsoft Foundry IQ**. It is live in Copilot Chat and demonstrably calls its tools end to end.

Its core idea is **one engine, two actors**: the same deterministic authorization-and-control engine governs both the human study staff (against the delegation timeline) and the Copilot agents (against regulatory controls).

## Features and functionality

- **Temporal authorization reconciliation** (`reconcile_authorization`, `check_authorization`) — deterministic date/credential logic that flags tasks performed before delegation was effective or PI-signed, expired GCP certifications, and undelegated performers. This is the differentiator: it checks authorization *at the time of the act*, not the existence of a document.
- **Copilot agent governance pipeline** (`inventory_agents` → `evaluate_agent` → `map_to_controls` → `generate_attestation`) — inventories the agents in a tenant, scores how each handles regulated data across weighted dimensions (e.g. audit-trail integrity, regulatory alignment, access appropriateness, data-classification coverage), and maps each gap to a named, cited control.
- **Grounded FDA-style validation package** — from the governance outputs, Palis assembles a structured Computer System Validation draft (Document Control, Validation Summary, Risk Register, URS/FS, Traceability Matrix, IQ/OQ/PQ draft protocols, Deviations, CAPA, Validation Conclusion). Every claim carries its tool source.
- **Grounded-only safety behavior** — Palis never asserts a regulatory requirement without a retrieved citation, labels findings "gap — review required" rather than "compliant/non-compliant," marks unavailable evidence as placeholders instead of fabricating it, and surfaces that it operates on synthetic demonstration data.

## How it uses Microsoft technology

- **Microsoft 365 Copilot** — Palis is a declarative agent surfaced in Copilot Chat. An `ai-plugin.json` action of type `RemoteMCPServer` connects the agent to the external MCP server, and Copilot performs the live tool calls. (Verified working end to end.)
- **Microsoft Foundry IQ** — the regulatory grounding layer. Control citations and grounded requirements are retrieved live from an Azure AI Search index using **extractive** retrieval (no generative LLM in the grounding path), so citations reflect the source corpus rather than model memory. This is the required IQ component and is demonstrated live in the governance and validation flows.

## Technology stack

Python; FastMCP (MCP server, streamable-HTTP); Microsoft 365 Agents Toolkit (declarative agent + RemoteMCPServer action); Azure AI Search as the Foundry IQ retrieval index (extractive); Microsoft Dev Tunnels (local-to-Copilot connectivity for the demo). Optional/roadmap: Microsoft Entra ID OAuth 2.0 for authenticated production access.

## Honest scope

Palis is **decision support and audit preparation, not certification or a system of record**. All demonstration data is synthetic. The grounded control set is focused (Part 11, HIPAA, GDPR special-category) rather than exhaustive, and the validation packages it produces are drafts that flag the evidence still required. Production use against real data would require authenticated access (OAuth/Entra), a hardened and expanded regulatory corpus, and a formal security review. The public repository ships a reference scorer; the production scoring methodology is proprietary.
