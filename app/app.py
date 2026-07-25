from __future__ import annotations

from io import BytesIO
from pathlib import Path
import json
import sys
from textwrap import dedent

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# =========================================================
# PROJECT SETUP
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from scripts.governance_rules import evaluate_governance_status

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "services.csv"

st.set_page_config(
    page_title="Enterprise Service Governance Catalog",
    page_icon="🛡️",
    layout="wide",
)


# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def load_data() -> pd.DataFrame:
    """Load the synthetic service inventory and apply governance rules."""
    raw_data = pd.read_csv(DATA_PATH)

    date_columns = [
        "last_review_date",
        "next_review_date",
        "target_action_date",
    ]

    for column in date_columns:
        if column in raw_data.columns:
            raw_data[column] = pd.to_datetime(
                raw_data[column],
                errors="coerce",
            )

    return evaluate_governance_status(raw_data)


df = load_data()


# =========================================================
# GENERAL HELPERS
# =========================================================

def split_items(value: object) -> list[str]:
    """Convert a semicolon-delimited value into a clean list."""
    if pd.isna(value):
        return []

    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]


def format_date(value: object) -> str:
    """Safely format a date for display."""
    if pd.isna(value):
        return "Not Available"

    return pd.to_datetime(value).strftime("%Y-%m-%d")


def yes_no(value: object) -> str:
    """Normalize truth-like values to Yes or No."""
    normalized = str(value).strip().lower()

    if normalized in {"yes", "true", "1"}:
        return "Yes"

    return "No"


def display_success_items(items: list[str]) -> None:
    """Display approved items in two columns."""
    if not items:
        st.warning("No approved items are documented.")
        return

    item_columns = st.columns(2)

    for index, item in enumerate(items):
        with item_columns[index % 2]:
            if item in {
                "No Enterprise Capabilities Approved",
                "No Enterprise Use Cases Approved",
            }:
                st.error(f"✖ {item}")
            else:
                st.success(f"✓ {item}")


def display_prohibited_items(items: list[str]) -> None:
    """Display prohibited items in two columns."""
    if not items:
        st.info("No prohibited uses are documented.")
        return

    item_columns = st.columns(2)

    for index, item in enumerate(items):
        with item_columns[index % 2]:
            st.error(f"✖ {item}")


def display_control_items(items: list[str]) -> None:
    """Display required security controls in three columns."""
    if not items:
        st.warning("No required security controls are documented.")
        return

    control_columns = st.columns(3)

    for index, item in enumerate(items):
        with control_columns[index % 3]:
            st.info(f"🛡️ {item}")


# =========================================================
# GOVERNANCE SCORE
# =========================================================

def calculate_governance_score(service: pd.Series) -> tuple[int, list[str]]:
    """
    Calculate a transparent governance score.

    The score begins at 100 and deductions are applied for
    architecture, approval, risk, evidence, and review issues.
    """
    score = 100
    deductions: list[str] = []

    approval_status = str(
        service.get("approval_status", "")
    ).strip()

    ea_approval = str(
        service.get("ea_approval", "")
    ).strip()

    cada_approval = str(
        service.get("cada_approval", "")
    ).strip()

    risk_level = str(
        service.get("risk_level", "")
    ).strip()

    if approval_status == "Not Approved":
        score -= 35
        deductions.append("-35: Service is not approved")

    elif approval_status == "Under Review":
        score -= 20
        deductions.append("-20: Service remains under review")

    elif approval_status == "Conditional":
        score -= 12
        deductions.append("-12: Service is conditionally approved")

    if ea_approval == "Pending":
        score -= 10
        deductions.append("-10: EA approval is pending")

    elif ea_approval == "Missing":
        score -= 15
        deductions.append("-15: EA approval is missing")

    if cada_approval == "Pending":
        score -= 10
        deductions.append("-10: CADA approval is pending")

    elif cada_approval == "Missing":
        score -= 15
        deductions.append("-15: CADA approval is missing")

    if bool(service.get("review_expired", False)):
        score -= 15
        deductions.append("-15: Governance review is expired")

    risk_deductions = {
        "Low": 0,
        "Medium": 5,
        "High": 12,
        "Critical": 20,
    }

    risk_deduction = risk_deductions.get(risk_level, 0)

    if risk_deduction:
        score -= risk_deduction
        deductions.append(
            f"-{risk_deduction}: {risk_level} risk classification"
        )

    if yes_no(
        service.get("risk_acceptance_required", "No")
    ) == "Yes":
        score -= 8
        deductions.append("-8: Formal risk acceptance is required")

    required_controls = split_items(
        service.get("required_controls", "")
    )

    if not required_controls:
        score -= 10
        deductions.append("-10: Required controls are undocumented")

    blockers = split_items(
        service.get("current_blockers", "")
    )

    active_blockers = [
        blocker
        for blocker in blockers
        if blocker.lower() != "no active blockers"
    ]

    if active_blockers:
        blocker_deduction = min(
            len(active_blockers) * 3,
            12,
        )

        score -= blocker_deduction
        deductions.append(
            f"-{blocker_deduction}: Active governance blockers"
        )

    return max(score, 0), deductions


def governance_score_label(score: int) -> str:
    """Translate the numeric governance score into a readiness label."""
    if score >= 90:
        return "Strong"

    if score >= 75:
        return "Acceptable"

    if score >= 60:
        return "Needs Attention"

    return "High Concern"


# =========================================================
# EVIDENCE CHECKLIST
# =========================================================

def build_evidence_checklist(
    service: pd.Series,
) -> list[dict[str, object]]:
    """Build a governance evidence checklist for the selected service."""
    required_controls = split_items(
        service.get("required_controls", "")
    )

    approved_use_cases = split_items(
        service.get("approved_use_cases", "")
    )

    approved_capabilities = split_items(
        service.get("approved_capabilities", "")
    )

    checklist = [
        {
            "Evidence Item": "Service owner documented",
            "Complete": bool(
                str(service.get("service_owner", "")).strip()
            ),
            "Evidence": service.get(
                "service_owner",
                "Not documented",
            ),
        },
        {
            "Evidence Item": "EA approval documented",
            "Complete": str(
                service.get("ea_approval", "")
            ).strip() == "Approved",
            "Evidence": service.get(
                "ea_approval",
                "Not documented",
            ),
        },
        {
            "Evidence Item": "CADA approval documented",
            "Complete": str(
                service.get("cada_approval", "")
            ).strip() == "Approved",
            "Evidence": service.get(
                "cada_approval",
                "Not documented",
            ),
        },
        {
            "Evidence Item": "Approved regions documented",
            "Complete": bool(
                str(service.get("approved_regions", "")).strip()
            ),
            "Evidence": service.get(
                "approved_regions",
                "Not documented",
            ),
        },
        {
            "Evidence Item": "Required controls documented",
            "Complete": len(required_controls) > 0,
            "Evidence": (
                f"{len(required_controls)} controls documented"
                if required_controls
                else "No controls documented"
            ),
        },
        {
            "Evidence Item": "Approved capabilities documented",
            "Complete": (
                len(approved_capabilities) > 0
                and "No Enterprise Capabilities Approved"
                not in approved_capabilities
            ),
            "Evidence": (
                f"{len(approved_capabilities)} capabilities documented"
                if approved_capabilities
                else "No capabilities documented"
            ),
        },
        {
            "Evidence Item": "Approved use cases documented",
            "Complete": (
                len(approved_use_cases) > 0
                and "No Enterprise Use Cases Approved"
                not in approved_use_cases
            ),
            "Evidence": (
                f"{len(approved_use_cases)} use cases documented"
                if approved_use_cases
                else "No use cases documented"
            ),
        },
        {
            "Evidence Item": "Review date is current",
            "Complete": not bool(
                service.get("review_expired", False)
            ),
            "Evidence": format_date(
                service.get("next_review_date")
            ),
        },
        {
            "Evidence Item": "Governance decision documented",
            "Complete": bool(
                str(
                    service.get(
                        "governance_decision",
                        "",
                    )
                ).strip()
            ),
            "Evidence": service.get(
                "governance_decision",
                "Not documented",
            ),
        },
        {
            "Evidence Item": "Recommended actions documented",
            "Complete": bool(
                str(
                    service.get(
                        "recommended_actions",
                        "",
                    )
                ).strip()
            ),
            "Evidence": (
                f"{len(split_items(service.get('recommended_actions', '')))} "
                "actions documented"
            ),
        },
    ]

    return checklist


# =========================================================
# CONTROL MAPPINGS
# =========================================================

def build_control_mappings(
    required_controls: list[str],
) -> pd.DataFrame:
    """
    Map common security controls to representative
    NIST SP 800-53 and CIS Controls.
    """
    mapping_library = {
        "encryption": {
            "NIST SP 800-53": "SC-13, SC-28",
            "CIS Controls": "3.11",
            "Purpose": "Protect sensitive data at rest and in transit",
        },
        "encryption at rest": {
            "NIST SP 800-53": "SC-28",
            "CIS Controls": "3.11",
            "Purpose": "Protect stored enterprise data",
        },
        "rbac": {
            "NIST SP 800-53": "AC-2, AC-3, AC-6",
            "CIS Controls": "5.4, 6.8",
            "Purpose": "Enforce role-based and least-privilege access",
        },
        "iam": {
            "NIST SP 800-53": "AC-2, AC-3, IA-2",
            "CIS Controls": "5, 6",
            "Purpose": "Manage identities, authentication, and access",
        },
        "least privilege": {
            "NIST SP 800-53": "AC-6",
            "CIS Controls": "5.4, 6.8",
            "Purpose": "Limit access to the minimum necessary",
        },
        "mfa": {
            "NIST SP 800-53": "IA-2",
            "CIS Controls": "6.3, 6.4, 6.5",
            "Purpose": "Strengthen authentication assurance",
        },
        "logging": {
            "NIST SP 800-53": "AU-2, AU-6, AU-12",
            "CIS Controls": "8",
            "Purpose": "Support monitoring, investigations, and auditability",
        },
        "audit logging": {
            "NIST SP 800-53": "AU-2, AU-6, AU-12",
            "CIS Controls": "8",
            "Purpose": "Capture and review security-relevant activity",
        },
        "prompt logging": {
            "NIST SP 800-53": "AU-2, AU-6",
            "CIS Controls": "8",
            "Purpose": "Support AI monitoring and traceability",
        },
        "private endpoint": {
            "NIST SP 800-53": "SC-7",
            "CIS Controls": "12.2",
            "Purpose": "Reduce public network exposure",
        },
        "private networking": {
            "NIST SP 800-53": "SC-7",
            "CIS Controls": "12",
            "Purpose": "Segment and protect network communications",
        },
        "private cluster": {
            "NIST SP 800-53": "SC-7",
            "CIS Controls": "12",
            "Purpose": "Restrict public access to cluster resources",
        },
        "network policies": {
            "NIST SP 800-53": "AC-4, SC-7",
            "CIS Controls": "12.2",
            "Purpose": "Control network traffic between workloads",
        },
        "backups": {
            "NIST SP 800-53": "CP-9, CP-10",
            "CIS Controls": "11",
            "Purpose": "Support service and data recovery",
        },
        "automated backups": {
            "NIST SP 800-53": "CP-9, CP-10",
            "CIS Controls": "11",
            "Purpose": "Maintain recoverable copies of critical data",
        },
        "versioning": {
            "NIST SP 800-53": "CP-9, SI-12",
            "CIS Controls": "11",
            "Purpose": "Support recovery and data restoration",
        },
        "key rotation": {
            "NIST SP 800-53": "SC-12",
            "CIS Controls": "3.11",
            "Purpose": "Reduce cryptographic key exposure",
        },
        "rotation": {
            "NIST SP 800-53": "IA-5, SC-12",
            "CIS Controls": "5.2",
            "Purpose": "Rotate credentials and cryptographic material",
        },
        "secrets management": {
            "NIST SP 800-53": "IA-5, SC-12",
            "CIS Controls": "5.2",
            "Purpose": "Protect credentials and application secrets",
        },
        "image scanning": {
            "NIST SP 800-53": "RA-5, SI-2",
            "CIS Controls": "7",
            "Purpose": "Identify vulnerabilities in container images",
        },
        "patching": {
            "NIST SP 800-53": "SI-2",
            "CIS Controls": "7",
            "Purpose": "Remediate software vulnerabilities",
        },
        "alerting": {
            "NIST SP 800-53": "SI-4, IR-4",
            "CIS Controls": "8, 13",
            "Purpose": "Notify teams about security and operational events",
        },
        "continuous monitoring": {
            "NIST SP 800-53": "CA-7, SI-4",
            "CIS Controls": "13",
            "Purpose": "Continuously identify control and threat conditions",
        },
        "data classification": {
            "NIST SP 800-53": "RA-2, MP-3",
            "CIS Controls": "3.2",
            "Purpose": "Apply protection based on data sensitivity",
        },
        "data loss prevention": {
            "NIST SP 800-53": "AC-4, SC-7",
            "CIS Controls": "3.13",
            "Purpose": "Reduce unauthorized data disclosure",
        },
        "human oversight": {
            "NIST SP 800-53": "AC-5, PM-14",
            "CIS Controls": "14",
            "Purpose": "Require human accountability for sensitive decisions",
        },
        "content filtering": {
            "NIST SP 800-53": "SI-3, SI-4",
            "CIS Controls": "9.2",
            "Purpose": "Detect and restrict unsafe content",
        },
        "block public access": {
            "NIST SP 800-53": "AC-3, SC-7",
            "CIS Controls": "3.3, 12",
            "Purpose": "Prevent unintended public exposure",
        },
        "approved region": {
            "NIST SP 800-53": "SA-9, SR-3",
            "CIS Controls": "15",
            "Purpose": "Maintain approved hosting and data residency boundaries",
        },
    }

    rows: list[dict[str, str]] = []

    for control in required_controls:
        normalized = control.strip().lower()

        mapping = mapping_library.get(
            normalized,
            {
                "NIST SP 800-53": "Organization-defined",
                "CIS Controls": "Organization-defined",
                "Purpose": "Enterprise-specific security requirement",
            },
        )

        rows.append(
            {
                "Required Control": control,
                "NIST SP 800-53": mapping["NIST SP 800-53"],
                "CIS Controls": mapping["CIS Controls"],
                "Purpose": mapping["Purpose"],
            }
        )

    return pd.DataFrame(rows)


# =========================================================
# APPROVAL TIMELINE
# =========================================================

def approval_step_status(
    service: pd.Series,
) -> list[dict[str, str]]:
    """Build the current governance approval timeline."""
    intake_status = "Complete"

    ea_value = str(
        service.get("ea_approval", "")
    ).strip()

    cada_value = str(
        service.get("cada_approval", "")
    ).strip()

    approval_value = str(
        service.get("approval_status", "")
    ).strip()

    if ea_value == "Approved":
        ea_status = "Complete"
    elif ea_value in {"Pending", "Missing"}:
        ea_status = "Current"
    else:
        ea_status = "Pending"

    if ea_value != "Approved":
        cada_status = "Pending"

    elif cada_value == "Approved":
        cada_status = "Complete"

    elif cada_value in {"Pending", "Missing"}:
        cada_status = "Current"

    else:
        cada_status = "Pending"

    if (
        ea_value == "Approved"
        and cada_value == "Approved"
    ):
        if approval_value == "Approved":
            final_status = "Complete"
        else:
            final_status = "Current"
    else:
        final_status = "Pending"

    return [
        {
            "name": "Intake",
            "status": intake_status,
        },
        {
            "name": "EA Review",
            "status": ea_status,
        },
        {
            "name": "CADA Review",
            "status": cada_status,
        },
        {
            "name": "Governance Decision",
            "status": final_status,
        },
    ]


def render_approval_timeline(
    service: pd.Series,
) -> None:
    """Render the governance approval timeline."""

    steps = approval_step_status(service)

    status_styles = {
        "Complete": {
            "background": "#174f36",
            "border": "#2e8b57",
            "symbol": "✓",
        },
        "Current": {
            "background": "#5a4517",
            "border": "#c89b2c",
            "symbol": "●",
        },
        "Pending": {
            "background": "#333842",
            "border": "#626a78",
            "symbol": "○",
        },
    }

    step_html = ""

    for step in steps:
        style = status_styles[step["status"]]

        step_html += dedent(
            f"""
            <div style="
                flex: 1;
                min-width: 150px;
                padding: 16px;
                margin: 4px;
                border-radius: 10px;
                background: {style['background']};
                border: 1px solid {style['border']};
                text-align: center;
            ">
                <div style="font-size: 24px;">
                    {style['symbol']}
                </div>
                <div style="font-weight: 700; margin-top: 5px;">
                    {step['name']}
                </div>
                <div style="font-size: 13px; opacity: 0.85;">
                    {step['status']}
                </div>
            </div>
            """
        ).strip()

    timeline_html = dedent(
        f"""
        <div style="
            display: flex;
            flex-wrap: wrap;
            align-items: stretch;
            justify-content: space-between;
            margin-bottom: 15px;
        ">
            {step_html}
        </div>
        """
    ).strip()

    st.markdown(
        timeline_html,
        unsafe_allow_html=True,
    )

# =========================================================
# ARCHITECTURE DIAGRAM
# =========================================================

def render_architecture_diagram(
    service: pd.Series,
) -> None:
    """Render a conceptual governance architecture diagram."""

    provider = str(
        service.get("cloud_provider", "Cloud")
    )

    service_name = str(
        service.get("service_name", "Cloud Service")
    )

    architecture_html = dedent(
        f"""
        <div style="
            border: 1px solid #3a4250;
            border-radius: 12px;
            padding: 22px;
            background: #111820;
            margin-top: 10px;
            margin-bottom: 15px;
        ">
            <div style="
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: center;
                gap: 12px;
                text-align: center;
            ">

                <div style="
                    padding: 14px 18px;
                    border-radius: 8px;
                    background: #243447;
                    min-width: 150px;
                ">
                    Business Request
                </div>

                <div style="font-size: 24px;">→</div>

                <div style="
                    padding: 14px 18px;
                    border-radius: 8px;
                    background: #3f3521;
                    min-width: 150px;
                ">
                    Architecture Review
                </div>

                <div style="font-size: 24px;">→</div>

                <div style="
                    padding: 14px 18px;
                    border-radius: 8px;
                    background: #3f3521;
                    min-width: 150px;
                ">
                    Security Controls
                </div>

                <div style="font-size: 24px;">→</div>

                <div style="
                    padding: 14px 18px;
                    border-radius: 8px;
                    background: #174f36;
                    min-width: 170px;
                ">
                    {provider}<br>{service_name}
                </div>

                <div style="font-size: 24px;">→</div>

                <div style="
                    padding: 14px 18px;
                    border-radius: 8px;
                    background: #243447;
                    min-width: 160px;
                ">
                    Logging &amp; Monitoring
                </div>

            </div>

            <div style="
                text-align: center;
                margin-top: 18px;
                font-size: 13px;
                opacity: 0.8;
            ">
                Conceptual portfolio diagram. A production implementation
                would link to approved logical architecture and data-flow documentation.
            </div>
        </div>
        """
    ).strip()

    st.markdown(
        architecture_html,
        unsafe_allow_html=True,
    )



# =========================================================
# GOVERNANCE DECISION PACKAGE
# =========================================================

def build_governance_decision_package(
    service: pd.Series,
) -> dict[str, list[str] | str]:
    """
    Build an executive-friendly explanation of why a service
    was approved, restricted, conditionally approved, or rejected.
    """

    approval_status = str(
        service.get("approval_status", "")
    ).strip()

    governance_readiness = str(
        service.get("governance_readiness", "")
    ).strip()

    risk_level = str(
        service.get("risk_level", "")
    ).strip()

    capabilities = split_items(
        service.get("approved_capabilities", "")
    )

    required_controls = split_items(
        service.get("required_controls", "")
    )

    approved_use_cases = split_items(
        service.get("approved_use_cases", "")
    )

    prohibited_use_cases = split_items(
        service.get("prohibited_use_cases", "")
    )

    blockers = split_items(
        service.get("current_blockers", "")
    )

    active_blockers = [
        blocker
        for blocker in blockers
        if blocker.lower() != "no active blockers"
    ]

    security_benefits = []

    benefit_keywords = {
        "encryption": "Protects sensitive enterprise data through encryption.",
        "rbac": "Supports role-based access and least-privilege enforcement.",
        "iam": "Supports centralized identity and access management.",
        "logging": "Provides auditability, monitoring, and investigation support.",
        "audit logging": "Captures security-relevant activity for review.",
        "private endpoint": "Reduces exposure to the public internet.",
        "private networking": "Restricts communication to approved network paths.",
        "backups": "Supports business continuity and data recovery.",
        "automated backups": "Provides consistent recovery protection.",
        "key rotation": "Reduces long-term exposure of cryptographic keys.",
        "secrets management": "Protects credentials and application secrets.",
        "least privilege": "Limits access to the minimum permissions required.",
        "mfa": "Strengthens authentication and reduces account-compromise risk.",
        "image scanning": "Identifies vulnerabilities before deployment.",
        "patching": "Supports timely remediation of known vulnerabilities.",
        "data classification": "Aligns controls with data sensitivity.",
        "human oversight": "Maintains accountability for sensitive decisions.",
        "content filtering": "Reduces exposure to unsafe or prohibited content.",
    }

    for control in required_controls:
        normalized_control = control.lower()

        for keyword, benefit in benefit_keywords.items():
            if keyword in normalized_control and benefit not in security_benefits:
                security_benefits.append(benefit)

    if not security_benefits:
        security_benefits.append(
            "Supports approved enterprise use when documented controls are implemented."
        )

    residual_risks = []

    if risk_level in {"High", "Critical"}:
        residual_risks.append(
            f"The service retains a {risk_level.lower()} residual-risk classification."
        )

    if active_blockers:
        residual_risks.extend(active_blockers)

    if approval_status == "Conditional":
        residual_risks.append(
            "Use is limited to documented conditions and approved use cases."
        )

    if approval_status == "Under Review":
        residual_risks.append(
            "The service must not be treated as fully approved until reviews are complete."
        )

    if approval_status == "Not Approved":
        residual_risks.append(
            "Deployment could create unacceptable governance or security exposure."
        )

    if not residual_risks:
        residual_risks = [
            "Misconfiguration or excessive access could weaken the approved control design.",
            "Control effectiveness depends on continued monitoring and annual review.",
        ]

    required_evidence = [
        "Documented service owner",
        "Approved architecture documentation",
        "EA review evidence",
        "CADA or cloud architecture approval",
        "Approved regions and use cases",
        "Required security-control documentation",
        "Current governance review date",
        "Risk decision and remediation actions",
    ]

    if risk_level == "Critical":
        required_evidence.append(
            "Executive risk-review approval"
        )

    if str(
        service.get(
            "risk_acceptance_required",
            "No",
        )
    ).strip().lower() == "yes":
        required_evidence.append(
            "Formal risk-acceptance record and compensating controls"
        )

    if (
        approval_status == "Approved"
        and governance_readiness == "Ready"
    ):
        why_decision = (
            "The service has completed the required architecture and "
            "governance reviews, has a documented owner, approved regions "
            "and use cases, required security controls, and a current "
            "review schedule."
        )

    elif approval_status == "Conditional":
        why_decision = (
            "The service provides a valid business capability, but approval "
            "is limited because one or more governance conditions, reviews, "
            "or risk treatments remain outstanding."
        )

    elif approval_status == "Under Review":
        why_decision = (
            "The service may provide business value, but architecture, "
            "security, risk, or responsible-use requirements are not yet "
            "complete enough to support final approval."
        )

    elif approval_status == "Not Approved":
        why_decision = (
            "The service does not currently satisfy enterprise governance "
            "requirements. Deployment is prohibited until the documented "
            "blockers are resolved and required approvals are completed."
        )

    else:
        why_decision = (
            "The decision is based on documented business need, architecture "
            "alignment, security-control coverage, residual risk, and evidence readiness."
        )

    business_need = (
        str(service.get("description", "")).strip()
        or (
            f"{service.get('service_name', 'This service')} provides "
            "an enterprise cloud capability for approved business workloads."
        )
    )

    return {
        "business_need": business_need,
        "why_decision": why_decision,
        "security_benefits": security_benefits,
        "residual_risks": residual_risks,
        "required_evidence": required_evidence,
        "approved_use_cases": approved_use_cases,
        "prohibited_use_cases": prohibited_use_cases,
        "capabilities": capabilities,
    }


def find_related_services(
    service: pd.Series,
    inventory: pd.DataFrame,
    limit: int = 5,
) -> list[str]:
    """
    Identify related services using cloud provider, category,
    owner, controls, and capabilities.
    """

    selected_name = str(
        service.get("service_name", "")
    )

    selected_provider = str(
        service.get("cloud_provider", "")
    )

    selected_category = str(
        service.get("category", "")
    )

    selected_owner = str(
        service.get("service_owner", "")
    )

    selected_controls = set(
        item.lower()
        for item in split_items(
            service.get("required_controls", "")
        )
    )

    selected_capabilities = set(
        item.lower()
        for item in split_items(
            service.get("approved_capabilities", "")
        )
    )

    scored_services = []

    for _, candidate in inventory.iterrows():
        candidate_name = str(
            candidate.get("service_name", "")
        )

        if candidate_name == selected_name:
            continue

        score = 0

        if str(candidate.get("cloud_provider", "")) == selected_provider:
            score += 2

        if str(candidate.get("category", "")) == selected_category:
            score += 3

        if str(candidate.get("service_owner", "")) == selected_owner:
            score += 2

        candidate_controls = set(
            item.lower()
            for item in split_items(
                candidate.get("required_controls", "")
            )
        )

        candidate_capabilities = set(
            item.lower()
            for item in split_items(
                candidate.get("approved_capabilities", "")
            )
        )

        score += len(
            selected_controls.intersection(candidate_controls)
        )

        score += len(
            selected_capabilities.intersection(
                candidate_capabilities
            )
        )

        if score > 0:
            scored_services.append(
                (candidate_name, score)
            )

    scored_services.sort(
        key=lambda item: (
            -item[1],
            item[0],
        )
    )

    return [
        service_name
        for service_name, _ in scored_services[:limit]
    ]

# =========================================================
# EXECUTIVE PDF
# =========================================================
def build_executive_pdf(
    service: pd.Series,
    governance_score: int,
    evidence_checklist: list[dict[str, object]],
    control_mappings: pd.DataFrame,
    decision_package: dict[str, list[str] | str],
) -> bytes:
    """Build a downloadable executive governance summary PDF."""
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=(
            f"Executive Governance Summary - "
            f"{service['service_name']}"
        ),
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="CenteredTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=20,
            leading=24,
            spaceAfter=14,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=7,
        )
    )

    story: list[object] = []

    story.append(
        Paragraph(
            "Executive Service Governance Summary",
            styles["CenteredTitle"],
        )
    )

    story.append(
        Paragraph(
            str(service["service_name"]),
            styles["Heading1"],
        )
    )

    story.append(
        Paragraph(
            "Synthetic portfolio demonstration — not an official "
            "enterprise approval record.",
            styles["Italic"],
        )
    )

    story.append(Spacer(1, 10))

    summary_data = [
        ["Service ID", str(service["service_id"])],
        ["Cloud Provider", str(service["cloud_provider"])],
        ["Category", str(service["category"])],
        ["Service Owner", str(service["service_owner"])],
        ["Approval Status", str(service["approval_status"])],
        [
            "Governance Readiness",
            str(service["governance_readiness"]),
        ],
        ["Risk Level", str(service["risk_level"])],
        [
            "Governance Score",
            f"{governance_score}/100 "
            f"({governance_score_label(governance_score)})",
        ],
        ["EA Approval", str(service["ea_approval"])],
        ["CADA Approval", str(service["cada_approval"])],
        [
            "Risk Acceptance Required",
            str(service["risk_acceptance_required"]),
        ],
        [
            "Next Review Date",
            format_date(service["next_review_date"]),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[2.1 * inch, 4.6 * inch],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#E8EDF3"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#9AA4B2"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(summary_table)
    story.append(
        Paragraph(
            "Business Need",
            styles["SectionHeading"],
        )
    )

    story.append(
        Paragraph(
            str(decision_package["business_need"]),
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            "Why This Governance Decision Was Made",
            styles["SectionHeading"],
        )
    )

    story.append(
        Paragraph(
            str(decision_package["why_decision"]),
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            "Security Benefits",
            styles["SectionHeading"],
        )
    )

    for benefit in decision_package["security_benefits"]:
        story.append(
            Paragraph(
                f"• {benefit}",
                styles["BodyText"],
            )
        )

    story.append(
        Paragraph(
            "Residual Risks",
            styles["SectionHeading"],
        )
    )

    for risk in decision_package["residual_risks"]:
        story.append(
            Paragraph(
                f"• {risk}",
                styles["BodyText"],
            )
        )

    story.append(
        Paragraph(
            "Required Governance Evidence",
            styles["SectionHeading"],
        )
    )

    for evidence_item in decision_package["required_evidence"]:
        story.append(
            Paragraph(
                f"• {evidence_item}",
                styles["BodyText"],
            )
        )
    story.append(
        Paragraph(
            "Governance Decision",
            styles["SectionHeading"],
        )
    )

    story.append(
        Paragraph(
            str(service["governance_decision"]),
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            "Current Blockers",
            styles["SectionHeading"],
        )
    )

    for blocker in split_items(
        service.get("current_blockers", "")
    ):
        story.append(
            Paragraph(
                f"• {blocker}",
                styles["BodyText"],
            )
        )

    story.append(
        Paragraph(
            "Recommended Actions",
            styles["SectionHeading"],
        )
    )

    for action in split_items(
        service.get("recommended_actions", "")
    ):
        story.append(
            Paragraph(
                f"• {action}",
                styles["BodyText"],
            )
        )

    story.append(
        Paragraph(
            "Approved Capabilities",
            styles["SectionHeading"],
        )
    )

    for capability in split_items(
        service.get("approved_capabilities", "")
    ):
        story.append(
            Paragraph(
                f"• {capability}",
                styles["BodyText"],
            )
        )

    story.append(
        Paragraph(
            "Required Security Controls",
            styles["SectionHeading"],
        )
    )

    for control in split_items(
        service.get("required_controls", "")
    ):
        story.append(
            Paragraph(
                f"• {control}",
                styles["BodyText"],
            )
        )

    story.append(PageBreak())

    story.append(
        Paragraph(
            "Evidence Readiness",
            styles["SectionHeading"],
        )
    )

    evidence_data = [
        ["Evidence Item", "Status", "Evidence"]
    ]

    for item in evidence_checklist:
        evidence_data.append(
            [
                str(item["Evidence Item"]),
                (
                    "Complete"
                    if item["Complete"]
                    else "Missing / Action Required"
                ),
                str(item["Evidence"]),
            ]
        )

    evidence_table = Table(
        evidence_data,
        colWidths=[
            2.3 * inch,
            1.5 * inch,
            3.0 * inch,
        ],
        repeatRows=1,
    )

    evidence_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#253447"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#9AA4B2"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(evidence_table)

    story.append(
        Paragraph(
            "Control Mappings",
            styles["SectionHeading"],
        )
    )

    if control_mappings.empty:
        story.append(
            Paragraph(
                "No control mappings were available.",
                styles["BodyText"],
            )
        )

    else:
        mapping_data = [
            [
                "Required Control",
                "NIST SP 800-53",
                "CIS Controls",
            ]
        ]

        for _, row in control_mappings.iterrows():
            mapping_data.append(
                [
                    str(row["Required Control"]),
                    str(row["NIST SP 800-53"]),
                    str(row["CIS Controls"]),
                ]
            )

        mapping_table = Table(
            mapping_data,
            colWidths=[
                2.8 * inch,
                2.0 * inch,
                1.8 * inch,
            ],
            repeatRows=1,
        )

        mapping_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#253447"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#9AA4B2"),
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(mapping_table)

    story.append(
        Paragraph(
            "Compensating Controls",
            styles["SectionHeading"],
        )
    )

    for control in split_items(
        service.get("compensating_controls", "")
    ):
        story.append(
            Paragraph(
                f"• {control}",
                styles["BodyText"],
            )
        )

    story.append(
        Paragraph(
            "Service Description",
            styles["SectionHeading"],
        )
    )

    story.append(
        Paragraph(
            str(service["description"]),
            styles["BodyText"],
        )
    )

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


# =========================================================
# PAGE HEADER
# =========================================================

st.title("Enterprise Service Governance Catalog")

st.caption(
    "A centralized governance decision portal for approved cloud services, "
    "capabilities, architecture reviews, evidence, security controls, "
    "risk exceptions, and remediation actions."
)

st.info(
    "Portfolio demonstration using synthetic data. "
    "This application does not represent an actual employer system."
)


# =========================================================
# ENTERPRISE KPI SUMMARY
# =========================================================

total_services = len(df)

governance_ready = int(
    (df["governance_readiness"] == "Ready").sum()
)

high_critical_risk = int(
    df["risk_level"].isin(
        ["High", "Critical"]
    ).sum()
)

expired_reviews = int(
    df["review_expired"].sum()
)

pending_actions = int(
    (
        (df["governance_readiness"] != "Ready")
        | df["review_expired"]
    ).sum()
)

risk_acceptance_count = int(
    df["risk_acceptance_required"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
    .eq("yes")
    .sum()
)

kpi_row_1 = st.columns(4)

kpi_row_1[0].metric(
    "Total Services",
    total_services,
)

kpi_row_1[1].metric(
    "Governance Ready",
    governance_ready,
)

kpi_row_1[2].metric(
    "High/Critical Risk",
    high_critical_risk,
)

kpi_row_1[3].metric(
    "Expired Reviews",
    expired_reviews,
)

kpi_row_2 = st.columns(2)

kpi_row_2[0].metric(
    "Pending Governance Actions",
    pending_actions,
)

kpi_row_2[1].metric(
    "Risk Acceptance Required",
    risk_acceptance_count,
)

st.divider()


# =========================================================
# SIDEBAR FILTERS
# =========================================================

with st.sidebar:
    st.header("Filters")

    search_term = st.text_input(
        "Search service, owner, capability, control, use case, or risk"
    )

    cloud_options = sorted(
        df["cloud_provider"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_clouds = st.multiselect(
        "Cloud provider",
        cloud_options,
    )

    approval_options = sorted(
        df["approval_status"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_statuses = st.multiselect(
        "Approval status",
        approval_options,
    )

    selected_risks = st.multiselect(
        "Risk level",
        ["Low", "Medium", "High", "Critical"],
    )

    selected_risk_acceptance = st.selectbox(
        "Risk acceptance required",
        ["All", "Yes", "No"],
    )


# =========================================================
# SEARCH AND FILTER LOGIC
# =========================================================

filtered = df.copy()

if search_term:
    searchable_columns = [
        "service_id",
        "service_name",
        "cloud_provider",
        "category",
        "approval_status",
        "approved_regions",
        "service_owner",
        "risk_level",
        "approved_capabilities",
        "approved_use_cases",
        "prohibited_use_cases",
        "required_controls",
        "nist_functions",
        "governance_decision",
        "current_blockers",
        "recommended_actions",
        "action_owner",
        "risk_acceptance_required",
        "compensating_controls",
        "description",
    ]

    existing_searchable_columns = [
        column
        for column in searchable_columns
        if column in filtered.columns
    ]

    search_index = (
        filtered[existing_searchable_columns]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
    )

    risk_acceptance_labels = (
        filtered["risk_acceptance_required"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .map(
            {
                "yes": (
                    "risk acceptance required "
                    "security exception required "
                    "formal risk acceptance"
                ),
                "no": (
                    "risk acceptance not required "
                    "no security exception required"
                ),
            }
        )
        .fillna("")
    )

    search_index = (
        search_index
        + " "
        + risk_acceptance_labels
    ).str.lower()

    normalized_search_term = (
        search_term.strip().lower()
    )

    filtered = filtered[
        search_index.str.contains(
            normalized_search_term,
            case=False,
            na=False,
            regex=False,
        )
    ]

if selected_clouds:
    filtered = filtered[
        filtered["cloud_provider"].isin(
            selected_clouds
        )
    ]

if selected_statuses:
    filtered = filtered[
        filtered["approval_status"].isin(
            selected_statuses
        )
    ]

if selected_risks:
    filtered = filtered[
        filtered["risk_level"].isin(
            selected_risks
        )
    ]

if selected_risk_acceptance != "All":
    filtered = filtered[
        filtered["risk_acceptance_required"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        == selected_risk_acceptance.lower()
    ]


# =========================================================
# MAIN TABS
# =========================================================

catalog_tab, intake_tab = st.tabs(
    [
        "Service Governance Catalog",
        "Submit for Governance Review",
    ]
)


# =========================================================
# MOCK GOVERNANCE INTAKE FORM
# =========================================================

with intake_tab:
    st.subheader("Submit a Service for Governance Review")

    st.caption(
        "Mock intake workflow demonstrating how a business or technology "
        "team could initiate architecture, security, and governance review."
    )

    with st.form(
        "governance_intake_form",
        clear_on_submit=False,
    ):
        form_col1, form_col2 = st.columns(2)

        with form_col1:
            requestor_name = st.text_input(
                "Requestor name"
            )

            business_unit = st.text_input(
                "Business unit"
            )

            requested_service = st.text_input(
                "Requested cloud service"
            )

            requested_provider = st.selectbox(
                "Cloud provider",
                [
                    "Azure",
                    "AWS",
                    "GCP",
                    "Other",
                ],
            )

            requested_region = st.text_input(
                "Requested deployment region"
            )

        with form_col2:
            data_classification = st.selectbox(
                "Highest data classification",
                [
                    "Public",
                    "Internal",
                    "Confidential",
                    "Restricted",
                ],
            )

            contains_pii = st.selectbox(
                "Will the solution process PII?",
                ["No", "Yes", "Unknown"],
            )

            internet_exposure = st.selectbox(
                "Will the service be publicly accessible?",
                ["No", "Yes", "Unknown"],
            )

            target_date = st.date_input(
                "Requested implementation date"
            )

            business_owner = st.text_input(
                "Business owner"
            )

        business_justification = st.text_area(
            "Business justification",
            height=110,
        )

        intended_use = st.text_area(
            "Intended use case",
            height=110,
        )

        required_integrations = st.text_area(
            "Required systems or integrations",
            height=90,
        )

        submitted = st.form_submit_button(
            "Submit for Governance Review",
            use_container_width=True,
        )

    if submitted:
        missing_fields = []

        required_values = {
            "Requestor name": requestor_name,
            "Business unit": business_unit,
            "Requested cloud service": requested_service,
            "Requested deployment region": requested_region,
            "Business owner": business_owner,
            "Business justification": business_justification,
            "Intended use case": intended_use,
        }

        for field_name, value in required_values.items():
            if not str(value).strip():
                missing_fields.append(field_name)

        if missing_fields:
            st.error(
                "Complete the following required fields: "
                + ", ".join(missing_fields)
            )

        else:
            intake_record = {
                "request_id": (
                    f"GOV-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
                ),
                "requestor_name": requestor_name,
                "business_unit": business_unit,
                "requested_service": requested_service,
                "cloud_provider": requested_provider,
                "requested_region": requested_region,
                "data_classification": data_classification,
                "contains_pii": contains_pii,
                "internet_exposure": internet_exposure,
                "target_date": str(target_date),
                "business_owner": business_owner,
                "business_justification": business_justification,
                "intended_use": intended_use,
                "required_integrations": required_integrations,
                "submission_status": "Submitted",
                "next_stage": "EA Review",
            }

            st.success(
                "Governance intake submitted successfully."
            )

            intake_col1, intake_col2, intake_col3 = st.columns(3)

            intake_col1.metric(
                "Request ID",
                intake_record["request_id"],
            )

            intake_col2.metric(
                "Status",
                "Submitted",
            )

            intake_col3.metric(
                "Next Stage",
                "EA Review",
            )

            st.info(
                "This portfolio form does not write to a production database. "
                "The JSON download simulates the payload that could be sent "
                "to ServiceNow, Jira, or another workflow platform."
            )

            st.download_button(
                label="Download Intake Record",
                data=json.dumps(
                    intake_record,
                    indent=2,
                ),
                file_name=(
                    f"{intake_record['request_id']}_governance_intake.json"
                ),
                mime="application/json",
                use_container_width=True,
            )


# =========================================================
# SERVICE CATALOG
# =========================================================

with catalog_tab:
    st.subheader("Service Inventory")

    st.caption(
        "Search by service name, capability, required control, "
        "approved use case, risk condition, or responsible owner."
    )

    inventory_columns = [
        "service_id",
        "service_name",
        "cloud_provider",
        "category",
        "approval_status",
        "governance_readiness",
        "risk_level",
        "governance_decision",
        "service_owner",
        "target_action_date",
    ]

    sorted_inventory = (
        filtered
        .sort_values(
            by=[
                "risk_score",
                "service_name",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )

    if sorted_inventory.empty:
        st.warning(
            "No services match the current filters."
        )

    else:
        st.dataframe(
            sorted_inventory[inventory_columns],
            use_container_width=True,
            hide_index=True,
        )

    service_options = (
        sorted_inventory["service_name"].tolist()
        if not sorted_inventory.empty
        else []
    )

    selected_service_name = st.selectbox(
        "Open a service governance profile",
        options=[
            "Select a service",
            *service_options,
        ],
        index=0,
    )

    if selected_service_name == "Select a service":
        st.info(
            "Select a service from the dropdown above "
            "to view its complete governance profile."
        )

    else:
        selected_service = sorted_inventory.loc[
            sorted_inventory["service_name"]
            == selected_service_name
        ].iloc[0]

        governance_score, score_deductions = (
            calculate_governance_score(
                selected_service
            )
        )

        evidence_checklist = build_evidence_checklist(
            selected_service
        )

        required_controls = split_items(
            selected_service["required_controls"]
        )

        control_mappings = build_control_mappings(
            required_controls
        )
        decision_package = build_governance_decision_package(
            selected_service
        )

        related_services = find_related_services(
             selected_service,
             df,
        )

        completed_evidence = sum(
            1
            for item in evidence_checklist
            if bool(item["Complete"])
        )

        evidence_percentage = int(
            (
                completed_evidence
                / len(evidence_checklist)
            )
            * 100
        )

        st.divider()

        st.subheader(
            f"Service Profile — "
            f"{selected_service['service_name']}"
        )

        profile_metrics = st.columns(5)

        profile_metrics[0].metric(
            "Approval Status",
            selected_service["approval_status"],
        )

        profile_metrics[1].metric(
            "Governance Readiness",
            selected_service["governance_readiness"],
        )

        profile_metrics[2].metric(
            "Risk Level",
            selected_service["risk_level"],
        )

        profile_metrics[3].metric(
            "Governance Score",
            f"{governance_score}/100",
        )

        profile_metrics[4].metric(
            "Evidence Complete",
            f"{evidence_percentage}%",
        )

        st.progress(
            governance_score / 100,
            text=(
                f"Governance Score: "
                f"{governance_score_label(governance_score)}"
            ),
        )


        # -------------------------------------------------
        # APPROVAL TIMELINE
        # -------------------------------------------------

        st.markdown("## Approval Timeline")

        render_approval_timeline(
            selected_service
        )


        # -------------------------------------------------
        # GOVERNANCE DECISION
        # -------------------------------------------------

        st.markdown("## Governance Decision")

        governance_decision = str(
            selected_service[
                "governance_decision"
            ]
        )

        if (
            selected_service["approval_status"]
            == "Approved"
            and selected_service[
                "governance_readiness"
            ]
            == "Ready"
        ):
            st.success(governance_decision)

        elif (
            selected_service["approval_status"]
            == "Not Approved"
        ):
            st.error(governance_decision)

        else:
            st.warning(governance_decision)

        decision_col1, decision_col2 = st.columns(2)

        with decision_col1:
            st.markdown("#### Current Blockers")

            blockers = split_items(
                selected_service[
                    "current_blockers"
                ]
            )

            if blockers == ["No active blockers"]:
                st.success("✓ No active blockers")

            elif blockers:
                for blocker in blockers:
                    st.error(f"• {blocker}")

            else:
                st.info(
                    "No blockers are documented."
                )

        with decision_col2:
            st.markdown("#### Recommended Actions")

            actions = split_items(
                selected_service[
                    "recommended_actions"
                ]
            )

            if actions:
                for action in actions:
                    st.info(f"→ {action}")

            else:
                st.info(
                    "No recommended actions are documented."
                )

        action_col1, action_col2, action_col3 = st.columns(3)

        action_col1.write(
            f"**Action Owner:** "
            f"{selected_service['action_owner']}"
        )

        action_col2.write(
            f"**Target Action Date:** "
            f"{format_date(selected_service['target_action_date'])}"
        )

        action_col3.write(
            f"**Risk Acceptance Required:** "
            f"{selected_service['risk_acceptance_required']}"
        )


        # -------------------------------------------------
        # GOVERNANCE SCORE DETAIL
        # -------------------------------------------------

        with st.expander(
            "How the Governance Score Was Calculated"
        ):
            st.write(
                "The score begins at 100. Deductions are applied "
                "for pending approvals, elevated risk, expired "
                "reviews, missing evidence, and active blockers."
            )

            if score_deductions:
                for deduction in score_deductions:
                    st.write(f"• {deduction}")

            else:
                st.success(
                    "No score deductions were applied."
                )


        # -------------------------------------------------
        # SERVICE DETAILS
        # -------------------------------------------------

        st.divider()

        detail_col1, detail_col2, detail_col3 = st.columns(3)

        with detail_col1:
            st.markdown("#### Service Information")

            st.write(
                f"**Service ID:** "
                f"{selected_service['service_id']}"
            )

            st.write(
                f"**Cloud Provider:** "
                f"{selected_service['cloud_provider']}"
            )

            st.write(
                f"**Category:** "
                f"{selected_service['category']}"
            )

            st.write(
                f"**Service Owner:** "
                f"{selected_service['service_owner']}"
            )

            st.write(
                f"**Approved Regions:** "
                f"{selected_service['approved_regions']}"
            )

        with detail_col2:
            st.markdown(
                "#### Architecture and Governance"
            )

            st.write(
                f"**EA Approval:** "
                f"{selected_service['ea_approval']}"
            )

            st.write(
                f"**CADA Approval:** "
                f"{selected_service['cada_approval']}"
            )

            st.write(
                f"**Approval Status:** "
                f"{selected_service['approval_status']}"
            )

            st.write(
                f"**Governance Readiness:** "
                f"{selected_service['governance_readiness']}"
            )

        with detail_col3:
            st.markdown("#### Risk and Review")

            st.write(
                f"**Risk Level:** "
                f"{selected_service['risk_level']}"
            )

            st.write(
                f"**Last Review Date:** "
                f"{format_date(selected_service['last_review_date'])}"
            )

            st.write(
                f"**Next Review Date:** "
                f"{format_date(selected_service['next_review_date'])}"
            )

            st.write(
                f"**Review Expired:** "
                f"{'Yes' if selected_service['review_expired'] else 'No'}"
            )



        # -------------------------------------------------
        # APPROVED CAPABILITIES
        # -------------------------------------------------

        st.markdown("## Approved Capabilities")

        display_success_items(
            split_items(
                selected_service[
                    "approved_capabilities"
                ]
            )
        )


        # -------------------------------------------------
        # USE CASES
        # -------------------------------------------------

        use_case_col1, use_case_col2 = st.columns(2)

        with use_case_col1:
            st.markdown("## Approved Use Cases")

            display_success_items(
                split_items(
                    selected_service[
                        "approved_use_cases"
                    ]
                )
            )

        with use_case_col2:
            st.markdown("## Prohibited Use Cases")

            display_prohibited_items(
                split_items(
                    selected_service[
                        "prohibited_use_cases"
                    ]
                )
            )


        # -------------------------------------------------
        # EVIDENCE CHECKLIST
        # -------------------------------------------------

        st.markdown("## Governance Evidence Checklist")

        evidence_display_rows = []

        for item in evidence_checklist:
            evidence_display_rows.append(
                {
                    "Status": (
                        "✅ Complete"
                        if item["Complete"]
                        else "❌ Missing / Action Required"
                    ),
                    "Evidence Item": item[
                        "Evidence Item"
                    ],
                    "Evidence": item["Evidence"],
                }
            )

        evidence_df = pd.DataFrame(
            evidence_display_rows
        )

        st.dataframe(
            evidence_df,
            use_container_width=True,
            hide_index=True,
        )

        st.progress(
            evidence_percentage / 100,
            text=(
                f"Evidence readiness: "
                f"{completed_evidence} of "
                f"{len(evidence_checklist)} items complete"
            ),
        )


        # -------------------------------------------------
        # REQUIRED CONTROLS
        # -------------------------------------------------

        st.markdown("## Required Security Controls")

        display_control_items(
            required_controls
        )


        # -------------------------------------------------
        # NIST CSF
        # -------------------------------------------------

        st.markdown("## NIST CSF Coverage")

        nist_functions = split_items(
            selected_service["nist_functions"]
        )

        if nist_functions:
            nist_columns = st.columns(
                min(
                    len(nist_functions),
                    6,
                )
            )

            for index, function in enumerate(
                nist_functions
            ):
                nist_columns[
                    index % len(nist_columns)
                ].metric(
                    "NIST Function",
                    function,
                )

        else:
            st.warning(
                "No NIST CSF mappings are documented."
            )


        # -------------------------------------------------
        # NIST 800-53 AND CIS
        # -------------------------------------------------

        st.markdown(
            "## NIST SP 800-53 and CIS Control Mappings"
        )

        st.caption(
            "Representative mappings for portfolio demonstration. "
            "Production mappings should be validated against the "
            "organization's official control library and implementation."
        )

        if control_mappings.empty:
            st.warning(
                "No control mappings are available."
            )

        else:
            st.dataframe(
                control_mappings,
                use_container_width=True,
                hide_index=True,
            )


        # -------------------------------------------------
        # RISK ACCEPTANCE
        # -------------------------------------------------

        st.markdown(
            "## Risk Acceptance and Compensating Controls"
        )

        requires_risk_acceptance = (
            yes_no(
                selected_service[
                    "risk_acceptance_required"
                ]
            )
            == "Yes"
        )

        if requires_risk_acceptance:
            st.warning(
                "Formal risk acceptance or exception review is required."
            )

            compensating_controls = split_items(
                selected_service[
                    "compensating_controls"
                ]
            )

            if compensating_controls:
                for control in compensating_controls:
                    st.write(f"• {control}")

            else:
                st.error(
                    "No compensating controls are documented."
                )

        else:
            st.success(
                "Formal risk acceptance is not currently required."
            )


        # -------------------------------------------------
        # DESCRIPTION
        # -------------------------------------------------

        st.markdown("## Service Description")

        st.info(
            selected_service["description"]
        )


        # -------------------------------------------------
        # GOVERNANCE DECISION PACKAGE
        # -------------------------------------------------

        st.markdown("## Governance Decision Package")

        st.caption(
            "Executive explanation of the business need, security value, "
            "residual risk, required evidence, and final governance rationale."
        )

        package_col1, package_col2 = st.columns(2)

        with package_col1:
            st.markdown("### Business Need")

            st.info(
                decision_package["business_need"]
            )

            st.markdown("### Why This Decision Was Made")

            if (
                selected_service["approval_status"] == "Approved"
                and selected_service["governance_readiness"] == "Ready"
            ):
                st.success(
                    decision_package["why_decision"]
                )

            elif selected_service["approval_status"] == "Not Approved":
                st.error(
                    decision_package["why_decision"]
                )

            else:
                st.warning(
                    decision_package["why_decision"]
                )

        with package_col2:
            st.markdown("### Security Benefits")

            for benefit in decision_package["security_benefits"]:
                st.success(f"✓ {benefit}")

            st.markdown("### Residual Risks")

            for risk in decision_package["residual_risks"]:
                st.warning(f"• {risk}")


        st.markdown("### Required Governance Evidence")

        evidence_columns = st.columns(2)

        for index, evidence_item in enumerate(
            decision_package["required_evidence"]
        ):
            with evidence_columns[index % 2]:
                st.info(f"📄 {evidence_item}")


        st.markdown("### Final Governance Decision")

        final_decision_col1, final_decision_col2 = st.columns(
            [2, 1]
        )

        with final_decision_col1:
            if (
                selected_service["approval_status"] == "Approved"
                and selected_service["governance_readiness"] == "Ready"
            ):
                st.success(
                    f"APPROVED — "
                    f"{selected_service['governance_decision']}"
                )

            elif selected_service["approval_status"] == "Not Approved":
                st.error(
                    f"NOT APPROVED — "
                    f"{selected_service['governance_decision']}"
                )

            else:
                st.warning(
                    f"{selected_service['approval_status'].upper()} — "
                    f"{selected_service['governance_decision']}"
                )

        with final_decision_col2:
            st.metric(
                "Governance Score",
                f"{governance_score}/100",
                governance_score_label(
                    governance_score
                ),
            )


        st.markdown("### Related Enterprise Services")

        if related_services:
            related_columns = st.columns(
                min(len(related_services), 3)
            )

            for index, related_service in enumerate(
                related_services
            ):
                related_columns[
                    index % len(related_columns)
                ].info(
                    f"🔗 {related_service}"
                )

        else:
            st.info(
                "No related enterprise services were identified."
            )

            # -------------------------------------------------
            # EXECUTIVE PDF DOWNLOAD
            # -------------------------------------------------

        st.markdown("## Executive Reporting")

        executive_pdf = build_executive_pdf(
            selected_service,
            governance_score,
            evidence_checklist,
            control_mappings,
            decision_package,
        )

        safe_service_name = (
            str(selected_service["service_name"])
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
        )

        st.download_button(
            label="Download Executive Governance PDF",
            data=executive_pdf,
            file_name=(
                f"{safe_service_name}_governance_summary.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
        )

      # =====================================================
    # LEADERSHIP EXCEPTIONS
    # =====================================================

    st.divider()

    st.subheader("Leadership Exceptions")

    st.caption(
        "Services requiring governance, architecture, "
        "risk, remediation, or review action."
    )

    exceptions = filtered[
        (
            filtered["governance_readiness"] != "Ready"
        )
        | (
            filtered["risk_acceptance_required"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            == "yes"
        )
    ].copy()

    exception_columns = [
        "service_name",
        "cloud_provider",
        "governance_decision",
        "risk_level",
        "current_blockers",
        "action_owner",
        "target_action_date",
        "risk_acceptance_required",
    ]

    if exceptions.empty:
        st.success(
            "No governance exceptions were found "
            "for the current filters."
        )

    else:
        exceptions = exceptions.sort_values(
            by=[
                "risk_score",
                "service_name",
            ],
            ascending=[
                False,
                True,
            ],
        )

        st.dataframe(
            exceptions[exception_columns],
            use_container_width=True,
            hide_index=True,
        )
