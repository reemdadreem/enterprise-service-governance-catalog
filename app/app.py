from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# Project setup
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from scripts.governance_rules import evaluate_governance_status

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "services.csv"

st.set_page_config(
    page_title="Enterprise Service Governance Catalog",
    page_icon="🛡️",
    layout="wide",
)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

@st.cache_data
def load_data() -> pd.DataFrame:
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


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def split_items(value: object) -> list[str]:
    """Convert a semicolon-delimited CSV value into clean items."""
    if pd.isna(value):
        return []

    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]


def format_date(value: object) -> str:
    """Format a date safely for display."""
    if pd.isna(value):
        return "Not Available"

    return pd.to_datetime(value).strftime("%Y-%m-%d")


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


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("Enterprise Service Governance Catalog")

st.caption(
    "A centralized governance decision portal for reviewing approved cloud "
    "services, capabilities, use cases, architecture approvals, security "
    "controls, risk exceptions, and required actions."
)


# ---------------------------------------------------------
# Enterprise KPI summary
# ---------------------------------------------------------

total_services = len(df)

governance_ready = int(
    (df["governance_readiness"] == "Ready").sum()
)

high_critical_risk = int(
    df["risk_level"].isin(["High", "Critical"]).sum()
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

risk_acceptance_required = int(
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
    risk_acceptance_required,
)

st.divider()


# ---------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Apply filters
# ---------------------------------------------------------

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
                    "exception review required "
                    "formal risk acceptance "
                    "security exception"
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

    normalized_search_term = search_term.strip().lower()

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
        filtered["cloud_provider"].isin(selected_clouds)
    ]

if selected_statuses:
    filtered = filtered[
        filtered["approval_status"].isin(selected_statuses)
    ]

if selected_risks:
    filtered = filtered[
        filtered["risk_level"].isin(selected_risks)
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


# ---------------------------------------------------------
# Service inventory
# ---------------------------------------------------------

st.subheader("Service Inventory")

st.caption(
    "Search by service name, capability, security control, approved use case, "
    "risk condition, or responsible owner."
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
        by=["risk_score", "service_name"],
        ascending=[False, True],
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


# ---------------------------------------------------------
# Service selector
# ---------------------------------------------------------

service_options = sorted_inventory["service_name"].tolist()

selected_service_name = st.selectbox(
    "Open a service governance profile",
    options=["Select a service"] + service_options,
    index=0,
)


# ---------------------------------------------------------
# Service governance profile
# ---------------------------------------------------------

if selected_service_name != "Select a service":

    selected_service = sorted_inventory.loc[
        sorted_inventory["service_name"]
        == selected_service_name
    ].iloc[0]

    st.divider()

    st.subheader(
        f"Service Profile — {selected_service['service_name']}"
    )

    profile_metrics = st.columns(4)

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
        "Cloud Provider",
        selected_service["cloud_provider"],
    )

    st.divider()


    # -----------------------------------------------------
    # Governance decision
    # -----------------------------------------------------

    st.markdown("## Governance Decision")

    governance_decision = str(
        selected_service["governance_decision"]
    )

    if (
        selected_service["approval_status"] == "Approved"
        and selected_service["governance_readiness"] == "Ready"
    ):
        st.success(governance_decision)

    elif selected_service["approval_status"] == "Not Approved":
        st.error(governance_decision)

    else:
        st.warning(governance_decision)

    decision_col1, decision_col2 = st.columns(2)

    with decision_col1:
        st.markdown("#### Current Blockers")

        blockers = split_items(
            selected_service["current_blockers"]
        )

        if blockers == ["No active blockers"]:
            st.success("✓ No active blockers")

        elif blockers:
            for blocker in blockers:
                st.error(f"• {blocker}")

        else:
            st.info("No blockers are documented.")

    with decision_col2:
        st.markdown("#### Recommended Actions")

        actions = split_items(
            selected_service["recommended_actions"]
        )

        if actions:
            for action in actions:
                st.info(f"→ {action}")

        else:
            st.info("No recommended actions are documented.")

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

    st.divider()


    # -----------------------------------------------------
    # Service details
    # -----------------------------------------------------

    detail_col1, detail_col2, detail_col3 = st.columns(3)

    with detail_col1:
        st.markdown("#### Service Information")

        st.write(
            f"**Service ID:** "
            f"{selected_service['service_id']}"
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
        st.markdown("#### Architecture and Governance")

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

        review_expired_text = (
            "Yes"
            if selected_service["review_expired"]
            else "No"
        )

        st.write(
            f"**Review Expired:** "
            f"{review_expired_text}"
        )


    # -----------------------------------------------------
    # Approved capabilities
    # -----------------------------------------------------

    st.markdown("## Approved Capabilities")

    display_success_items(
        split_items(
            selected_service["approved_capabilities"]
        )
    )


    # -----------------------------------------------------
    # Approved and prohibited use cases
    # -----------------------------------------------------

    use_case_col1, use_case_col2 = st.columns(2)

    with use_case_col1:
        st.markdown("## Approved Use Cases")

        display_success_items(
            split_items(
                selected_service["approved_use_cases"]
            )
        )

    with use_case_col2:
        st.markdown("## Prohibited Use Cases")

        display_prohibited_items(
            split_items(
                selected_service["prohibited_use_cases"]
            )
        )


    # -----------------------------------------------------
    # Required security controls
    # -----------------------------------------------------

    st.markdown("## Required Security Controls")

    display_control_items(
        split_items(
            selected_service["required_controls"]
        )
    )


    # -----------------------------------------------------
    # NIST CSF coverage
    # -----------------------------------------------------

    st.markdown("## NIST CSF Coverage")

    nist_functions = split_items(
        selected_service["nist_functions"]
    )

    if nist_functions:
        nist_columns = st.columns(
            min(len(nist_functions), 6)
        )

        for index, function in enumerate(nist_functions):
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


    # -----------------------------------------------------
    # Risk acceptance and compensating controls
    # -----------------------------------------------------

    st.markdown(
        "## Risk Acceptance and Compensating Controls"
    )

    requires_risk_acceptance = (
        str(
            selected_service[
                "risk_acceptance_required"
            ]
        )
        .strip()
        .lower()
        == "yes"
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


    # -----------------------------------------------------
    # Service description
    # -----------------------------------------------------

    st.markdown("## Service Description")

    st.info(
        selected_service["description"]
    )

else:
    st.info(
        "Select a service from the dropdown above "
        "to view its complete governance profile."
    )


# ---------------------------------------------------------
# Leadership exceptions
# ---------------------------------------------------------

st.divider()

st.subheader("Leadership Exceptions")

st.caption(
    "Services requiring governance, architecture, risk, "
    "remediation, or review action."
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
        by=["risk_score", "service_name"],
        ascending=[False, True],
    )

    st.dataframe(
        exceptions[exception_columns],
        use_container_width=True,
        hide_index=True,
    )