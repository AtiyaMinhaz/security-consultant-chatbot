from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

from retriever import RetrievalResult


@dataclass
class BusinessProfile:
    industry: str = "Unknown"
    geography: str = "Unknown"
    handles_pii: bool = True
    handles_payments: bool = False
    has_employees: bool = False
    uses_cloud: bool = True
    stage: str = "Early (idea/MVP)"


def _yesno(value: bool) -> str:
    return "Yes" if value else "No"


def build_discovery_questions() -> List[str]:
    return [
        "What is your business industry (e.g., e-commerce, healthcare, fintech, SaaS)?",
        "Where will you operate (countries/states)?",
        "Will you collect personal data (names, emails, phone, address)? (yes/no)",
        "Will you process payments (credit cards)? (yes/no)",
        "Will you have employees/contractors with system access? (yes/no)",
        "Will you use cloud services (AWS/Azure/GCP)? (yes/no)",
        "What stage are you at (idea/MVP/launch/growing)?",
    ]


def parse_profile(answers: Dict[str, str]) -> BusinessProfile:
    # Defensive parsing. If user types anything weird, we still produce a profile.
    def is_yes(x: str) -> bool:
        return x.strip().lower() in {"yes", "y", "true", "1"}

    return BusinessProfile(
        industry=answers.get("industry", "Unknown").strip() or "Unknown",
        geography=answers.get("geography", "Unknown").strip() or "Unknown",
        handles_pii=is_yes(answers.get("pii", "yes")),
        handles_payments=is_yes(answers.get("payments", "no")),
        has_employees=is_yes(answers.get("employees", "no")),
        uses_cloud=is_yes(answers.get("cloud", "yes")),
        stage=answers.get("stage", "Early (idea/MVP)").strip() or "Early (idea/MVP)",
    )


def consultant_response_offline(
    user_message: str,
    profile: BusinessProfile,
    retrieved: List[RetrievalResult],
) -> str:
    """
    Offline consultant response: structured, action-oriented, and standards-aware.
    This does NOT require any external LLM.
    """
    # Decide compliance signals
    compliance = []
    if profile.handles_payments:
        compliance.append("PCI DSS (if you store/process card data)")
    if "health" in profile.industry.lower():
        compliance.append("HIPAA (if you handle PHI in the U.S.)")
    if "eu" in profile.geography.lower() or "europe" in profile.geography.lower():
        compliance.append("GDPR (privacy obligations in the EU/EEA)")
    if profile.handles_pii:
        compliance.append("Privacy policy + data protection obligations (PII)")

    compliance_line = " | ".join(compliance) if compliance else "Baseline security + privacy hygiene"

    # Convert retrieved to short citations (not legal citations, just “source file” references)
    top_sources = [f"{r.source} (score {r.score:.2f})" for r in retrieved[:3]] or ["(no KB match yet)"]

    # Policy pack recommendations
    policy_pack = [
        "Information Security Policy (top-level intent and governance)",
        "Access Control Policy (least privilege, MFA, joiner/mover/leaver)",
        "Acceptable Use Policy (employees/contractors expectations)",
        "Data Classification & Handling Policy (PII labeling + storage rules)",
        "Incident Response Plan (detect, triage, contain, recover, lessons learned)",
        "Vendor/Supplier Risk Policy (SaaS due diligence, DPAs, security reviews)",
        "Backup & Recovery Policy (RPO/RTO, testing, immutable backups)",
        "Change Management Policy (controlled releases, approvals, rollback)",
        "Logging & Monitoring Standard (what you log, retention, alerting)",
    ]
    if profile.handles_payments:
        policy_pack.append("Payment Security Standard (scope, segmentation, tokenization guidance)")

    controls_mvp = [
        "MFA everywhere (email, admin panels, cloud console, GitHub)",
        "Password manager + unique credentials",
        "Role-based access control (RBAC) and least privilege",
        "Secure configuration baseline (CIS-style hardening where applicable)",
        "Central logging for critical systems + basic alerting",
        "Vulnerability management: patch cadence + dependency scanning",
        "Backups: encrypted, tested restores, defined RPO/RTO",
        "Encryption in transit (TLS) and at rest for sensitive data",
    ]

    evidence = [
        "Policy documents stored in Git (versioned) + approval log",
        "Access reviews (quarterly) + offboarding checklist",
        "Incident tabletop exercise notes (at least 1 per quarter initially)",
        "Asset inventory (systems, SaaS, endpoints) with owners",
        "Risk register (top 10 risks, mitigations, owners, due dates)",
    ]

    # Build response
    lines = []
    lines.append("**Executive Advisory (Consultant Mode)**")
    lines.append("")
    lines.append(f"**Your current operating profile:**")
    lines.append(f"- Industry: {profile.industry}")
    lines.append(f"- Geography: {profile.geography}")
    lines.append(f"- Handles PII: {_yesno(profile.handles_pii)}")
    lines.append(f"- Handles payments: {_yesno(profile.handles_payments)}")
    lines.append(f"- Employees/contractors: {_yesno(profile.has_employees)}")
    lines.append(f"- Cloud usage: {_yesno(profile.uses_cloud)}")
    lines.append(f"- Stage: {profile.stage}")
    lines.append("")
    lines.append(f"**Compliance pressure signals:** {compliance_line}")
    lines.append("")
    lines.append("**What you should implement first (0–30 days):**")
    for c in controls_mvp:
        lines.append(f"- {c}")
    lines.append("")
    lines.append("**Policy + standards baseline you should publish internally (starter pack):**")
    for p in policy_pack:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("**Pragmatic mapping to standards (so you look enterprise-ready):**")
    lines.append("- Use **NIST CSF** for a plain-English security program structure (Identify/Protect/Detect/Respond/Recover).")
    lines.append("- Use **CIS Controls** as your technical control checklist (what to actually deploy).")
    lines.append("- Use **ISO 27001** concepts for governance (roles, risk treatment, documented processes).")
    lines.append("- If customers ask for assurance, align evidence to **SOC 2** style controls (Security, Availability, Confidentiality, etc.).")
    lines.append("")
    lines.append("**Evidence you should be able to show an investor/customer (lightweight, high-impact):**")
    for e in evidence:
        lines.append(f"- {e}")
    lines.append("")
    lines.append("**Based on your question, here are the most relevant internal references I used:**")
    for s in top_sources:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("**Next question (so I can tailor the plan):** What product are you building (web app, mobile app, internal tool), and what are your top 3 data types (e.g., email, payment, location, health)?")
    lines.append("")
    lines.append("_Note: This is security guidance, not legal advice._")

    return "\n".join(lines)


def try_ollama_generate(prompt: str, model: str = "llama3") -> Optional[str]:
    """
    Optional: If the user has Ollama running locally, we can generate more natural language.
    Ollama default endpoint is http://localhost:11434/api/generate

    If not available, return None and we fall back to offline.
    """
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
        return data.get("response")
    except Exception:
        return None


def consultant_response(
    user_message: str,
    profile: BusinessProfile,
    retrieved: List[RetrievalResult],
    use_local_llm: bool = False,
    ollama_model: str = "llama3",
) -> str:
    """
    If use_local_llm=True and Ollama is running, it will improve tone.
    Otherwise it returns a strong offline consultant response.
    """
    offline = consultant_response_offline(user_message, profile, retrieved)

    if not use_local_llm:
        return offline

    # Build a grounded prompt that includes retrieval snippets (but stays concise)
    kb_snippets = "\n\n".join(
        [f"[SOURCE: {r.source}]\n{r.text[:1200]}" for r in retrieved[:3]]
    )
    prompt = f"""
You are a security compliance consultant advising a first-time business owner.
Be crisp, business-friendly, and implementation-focused.
Do not invent laws. If unsure, say what to verify.

BUSINESS PROFILE:
- Industry: {profile.industry}
- Geography: {profile.geography}
- Handles PII: {profile.handles_pii}
- Handles payments: {profile.handles_payments}
- Employees/contractors: {profile.has_employees}
- Cloud usage: {profile.uses_cloud}
- Stage: {profile.stage}

USER QUESTION:
{user_message}

INTERNAL REFERENCE SNIPPETS:
{kb_snippets}

Deliver:
1) Top priorities (0–30 days)
2) Policies to create
3) Standards mapping (NIST CSF, CIS, ISO 27001, SOC 2)
4) Evidence/artifacts to retain
End with 1 targeted follow-up question.
"""
    llm = try_ollama_generate(prompt=prompt.strip(), model=ollama_model)
    return llm.strip() if llm else offline
