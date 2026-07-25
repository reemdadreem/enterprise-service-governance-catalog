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
# Load and prepare data
# ---------------------------------------------------------

@st.cache_data
def load_data() -> pd.DataFrame:
    raw_data = pd.read_csv(DATA_PATH)
    return evaluate_governance_status(raw_data)


df = load_data()


# ---------------------------------------------------------
# Page header
# ---------------------------------------------------------

st.title("Enterprise Service Governance Catalog")

st.caption(
    "Centralized visibility into approved services, ownership, architecture "
    "approvals, approved capabilities, risk, regions, and review readiness."
)


# ---------------------------------------------------------
# KPI summary
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

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total Services",
    total_services,
)

c2.metric(
    "Governance Ready",
    governance_ready,
)

c3.metric(
    "High/Critical Risk",
    high_critical_risk,
)

c4.metric(
    "Expired Reviews",
    expired_reviews,
)

st.divider()


# ---------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------

with st.sidebar:
    st.header("Filters")

    search_term = st.text_input(
        "Search service, owner, capability, or description"
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


# ---------------------------------------------------------
# Apply filters
# ---------------------------------------------------------

filtered = df.copy()

if search_term:
    search_mask = (
        filtered["service_name"].str.contains(
            search_term,
            case=False,
            na=False,
        )
        | filtered["service_owner"].str.contains(
            search_term,
            case=False,
            na=False,
        )
        | filtered["description"].str.contains(
            search_term,
            case=False,
            na=False,
        )
        | filtered["approved_capabilities"].str.contains(
            search_term,
            case=False,
            na=False,
        )
    )

    filtered = filtered[search_mask]

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


# ---------------------------------------------------------
# Service inventory
# ---------------------------------------------------------

st.subheader("Service Inventory")

st.caption(
    "Filter the inventory and select a service from the dropdown "
    "to view its complete governance profile."
)

inventory_columns = [
    "service_id",
    "service_name",
    "cloud_provider",
    "category",
    "approval_status",
    "governance_readiness",
    "approved_regions",
    "approved_capabilities",
    "service_owner",
    "ea_approval",
    "cada_approval",
    "risk_level",
    "next_review_date",
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
# Service profile selector
# ---------------------------------------------------------

service_options = sorted_inventory["service_name"].tolist()

selected_service_name = st.selectbox(
    "Open a service governance profile",
    options=["Select a service"] + service_options,
    index=0,
)


# ---------------------------------------------------------
# Selected service governance profile
# ---------------------------------------------------------

if selected_service_name != "Select a service":

    selected_service = sorted_inventory.loc[
        sorted_inventory["service_name"]
        == selected_service_name
    ].iloc[0]

    st.divider()

    st.subheader(
        f"Service Profile — "
        f"{selected_service['service_name']}"
    )

    status_col1, status_col2, status_col3, status_col4 = (
        st.columns(4)
    )

    status_col1.metric(
        "Approval Status",
        selected_service["approval_status"],
    )

    status_col2.metric(
        "Governance Readiness",
        selected_service["governance_readiness"],
    )

    status_col3.metric(
        "Risk Level",
        selected_service["risk_level"],
    )

    status_col4.metric(
        "Cloud Provider",
        selected_service["cloud_provider"],
    )

    st.divider()

    profile_col1, profile_col2, profile_col3 = st.columns(3)

    with profile_col1:
        st.markdown("#### Service Information")

        st.write(
            f"**Service ID:** "
            f"{selected_service['service_id']}"
        )

        st.write(
            f"**Service Name:** "
            f"{selected_service['service_name']}"
        )

        st.write(
            f"**Category:** "
            f"{selected_service['category']}"
        )

        st.write(
            f"**Service Owner:** "
            f"{selected_service['service_owner']}"
        )

    with profile_col2:
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

    with profile_col3:
        st.markdown("#### Risk and Review")

        st.write(
            f"**Risk Level:** "
            f"{selected_service['risk_level']}"
        )

        st.write(
            f"**Approved Regions:** "
            f"{selected_service['approved_regions']}"
        )

        next_review_date = selected_service[
            "next_review_date"
        ]

        if pd.notna(next_review_date):
            formatted_review_date = (
                next_review_date.strftime("%Y-%m-%d")
            )
        else:
            formatted_review_date = "Not Available"

        st.write(
            f"**Next Review Date:** "
            f"{formatted_review_date}"
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

    st.markdown("#### Approved Capabilities")

    raw_capabilities = str(
        selected_service["approved_capabilities"]
    )

    capabilities = [
        capability.strip()
        for capability in raw_capabilities.split(";")
        if capability.strip()
    ]

    if not capabilities:
        st.warning(
            "No approved capabilities are documented "
            "for this service."
        )

    else:
        capability_columns = st.columns(2)

        for index, capability in enumerate(capabilities):

            target_column = capability_columns[
                index % 2
            ]

            with target_column:

                if (
                    capability
                    == "No Enterprise Capabilities Approved"
                ):
                    st.error(
                        f"✖ {capability}"
                    )

                else:
                    st.success(
                        f"✓ {capability}"
                    )


    # -----------------------------------------------------
    # Service description
    # -----------------------------------------------------

    st.markdown("#### Service Description")

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
    "Services that require governance, architecture, "
    "risk, or review action."
)

exceptions = filtered[
    filtered["governance_readiness"] != "Ready"
].copy()

exception_columns = [
    "service_name",
    "cloud_provider",
    "governance_readiness",
    "risk_level",
    "service_owner",
    "next_review_date",
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