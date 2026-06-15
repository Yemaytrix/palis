"""
authorization_reconciler.py
---------------------------
THE DIFFERENTIATOR. Existing eReg/eISF tools (Veeva, Complion, Florence) manage the
Delegation of Authority Log as a *document* — they store, version, e-sign, and remind.
What they largely do NOT do is reconcile *what actually happened* against *what was
authorized at the moment it happened*. That temporal gap is where real deviations hide:
a coordinator consents a participant before being added to the DOAL, or before the PI
signs it. The DOAL looks valid today; the activity was unauthorized when it occurred.

This module reconciles the activity log against the DOAL authorization timeline and
flags temporal authorization failures, each grounded in a cited control and accompanied
by an auto-drafted deviation note. It also supports a PROACTIVE pre-task check
(prevention, not just detection).

Reuses control_library.py so every finding carries a named, citable control.
"""

from dataclasses import dataclass, field
from datetime import date


def _d(s: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD)."""
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


@dataclass
class AuthFinding:
    event_id: str
    staff_id: str
    task: str
    severity: str          # "high" | "medium"
    control_id: str        # resolves against control_library.CONTROLS
    rationale: str
    deviation_note: str     # auto-drafted note-to-file text


def _doal_entry(doal: list, staff_id: str):
    for e in doal:
        if e["staff_id"] == staff_id:
            return e
    return None


def reconcile_activity(study: dict) -> list[AuthFinding]:
    """
    Walk the activity log and reconcile each event against the DOAL.
    Each rule ties a temporal/authorization condition to a named control and drafts
    the deviation language a site would otherwise have to write by hand.
    """
    findings: list[AuthFinding] = []
    doal = study["doal"]

    for ev in study["activity_log"]:
        sid = ev["performed_by"]
        task = ev["task"]
        when = _d(ev["date"])
        entry = _doal_entry(doal, sid)

        # Rule 0 — performer not on the DOAL at all.
        if entry is None:
            findings.append(AuthFinding(
                event_id=ev["event_id"], staff_id=sid, task=task,
                severity="high", control_id="GCP_DELEGATION",
                rationale=(f"{sid} performed '{task}' on {ev['date']} but is not listed "
                           f"on the Delegation of Authority Log for {study['study']}."),
                deviation_note=(f"DEVIATION (note to file): On {ev['date']}, {sid} performed "
                                f"'{task}' for {ev.get('subject','a subject')} without any "
                                f"delegated authority recorded on the DOAL. Per ICH E6(R3), "
                                f"trial tasks may be performed only by appropriately qualified, "
                                f"delegated individuals. Corrective action: add to DOAL with PI "
                                f"authorization, assess data integrity impact, report per SOP."),
            ))
            continue

        # Rule 1 — task performed BEFORE the delegation was effective.
        eff = _d(entry["delegation_effective"])
        if when < eff:
            findings.append(AuthFinding(
                event_id=ev["event_id"], staff_id=sid, task=task,
                severity="high", control_id="GCP_DELEGATION",
                rationale=(f"{sid} performed '{task}' on {ev['date']}, but delegation became "
                           f"effective {entry['delegation_effective']} — the task occurred "
                           f"before authorization."),
                deviation_note=(f"DEVIATION (note to file): {sid} performed '{task}' on "
                                f"{ev['date']}, prior to the DOAL delegation effective date of "
                                f"{entry['delegation_effective']}. The activity was not authorized "
                                f"at the time it occurred (ICH E6(R3) delegation). Assess impact on "
                                f"subject {ev.get('subject','')} and data integrity; report per SOP."),
            ))

        # Rule 2 — PI signature missing or dated AFTER the activity.
        pi_sig = entry.get("pi_signature_date")
        if not pi_sig:
            findings.append(AuthFinding(
                event_id=ev["event_id"], staff_id=sid, task=task,
                severity="high", control_id="P11_ESIGN",
                rationale=(f"DOAL entry for {sid} has no PI signature; the delegation under which "
                           f"'{task}' was performed on {ev['date']} is not PI-authorized."),
                deviation_note=(f"DEVIATION (note to file): The DOAL delegation for {sid} lacks the "
                                f"required PI signature. The PI must personally sign each delegation; "
                                f"activity performed under an unsigned delegation is not validly "
                                f"authorized (21 CFR 11.50/11.100; ICH E6(R3)). Obtain PI signature "
                                f"and assess affected activity."),
            ))
        elif _d(pi_sig) > when:
            findings.append(AuthFinding(
                event_id=ev["event_id"], staff_id=sid, task=task,
                severity="high", control_id="P11_ESIGN",
                rationale=(f"PI signed {sid}'s delegation on {pi_sig}, AFTER '{task}' was performed "
                           f"on {ev['date']} — the authorization was not in place at the time."),
                deviation_note=(f"DEVIATION (note to file): The PI signature authorizing {sid}'s "
                                f"delegation is dated {pi_sig}, after the {ev['date']} '{task}'. The "
                                f"delegation was not validly signed when the activity occurred "
                                f"(21 CFR 11.50/11.100; ICH E6(R3)). Document and assess impact."),
            ))

        # Rule 3 — task outside the delegated scope.
        if task not in entry.get("delegated_tasks", []):
            findings.append(AuthFinding(
                event_id=ev["event_id"], staff_id=sid, task=task,
                severity="high", control_id="GCP_DELEGATION",
                rationale=(f"{sid} performed '{task}' on {ev['date']}, which is outside their "
                           f"delegated tasks {entry.get('delegated_tasks', [])}."),
                deviation_note=(f"DEVIATION (note to file): {sid} performed '{task}' on {ev['date']}, "
                                f"a task not delegated to them on the DOAL. Per ICH E6(R3), only "
                                f"delegated tasks may be performed. Assess and report."),
            ))

        # Rule 4 — GCP certification expired before the activity.
        gcp_exp = entry.get("credentials", {}).get("gcp_cert_expiry")
        if gcp_exp and _d(gcp_exp) < when:
            findings.append(AuthFinding(
                event_id=ev["event_id"], staff_id=sid, task=task,
                severity="high", control_id="GCP_DELEGATION",
                rationale=(f"{sid} performed '{task}' on {ev['date']} with a GCP certification that "
                           f"expired {gcp_exp} — not appropriately qualified at the time."),
                deviation_note=(f"DEVIATION (note to file): {sid} performed '{task}' on {ev['date']} "
                                f"while their GCP certification was expired (expiry {gcp_exp}). ICH "
                                f"E6(R3) requires appropriately qualified personnel. Re-certify and "
                                f"assess affected activity."),
            ))

    return findings


def check_authorization(study: dict, staff_id: str, task: str, proposed_date: str) -> dict:
    """
    PROACTIVE pre-task gate (prevention, not detection). Call BEFORE a task is performed:
    returns allow/block plus the specific reasons, so a deviation is prevented rather than
    documented after the fact.
    """
    entry = _doal_entry(study["doal"], staff_id)
    when = _d(proposed_date)
    reasons = []

    if entry is None:
        reasons.append(f"{staff_id} is not on the DOAL.")
        return {"authorized": False, "reasons": reasons}

    if when < _d(entry["delegation_effective"]):
        reasons.append(f"Delegation not effective until {entry['delegation_effective']}.")
    pi_sig = entry.get("pi_signature_date")
    if not pi_sig:
        reasons.append("DOAL delegation is not PI-signed.")
    elif _d(pi_sig) > when:
        reasons.append(f"PI signature dated {pi_sig} is after the proposed date.")
    if task not in entry.get("delegated_tasks", []):
        reasons.append(f"'{task}' is not in delegated tasks {entry.get('delegated_tasks', [])}.")
    gcp_exp = entry.get("credentials", {}).get("gcp_cert_expiry")
    if gcp_exp and _d(gcp_exp) < when:
        reasons.append(f"GCP certification expired {gcp_exp}.")

    return {"authorized": len(reasons) == 0, "reasons": reasons or ["All authorization checks passed."]}
