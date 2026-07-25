from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "services.csv"


SERVICES = [
    {
        "service_id": "SVC-001",
        "service_name": "Azure Key Vault",
        "cloud_provider": "Azure",
        "category": "Security",
        "approval_status": "Approved",
        "approved_regions": "East US;West US 2",
        "service_owner": "Cloud Security",
        "last_review_date": "2026-05-20",
        "next_review_date": "2027-05-20",
        "ea_approval": "Approved",
        "cada_approval": "Approved",
        "risk_level": "Low",
        "approved_capabilities": (
            "Secrets Management;Key Management;"
            "Certificate Management;Key Rotation"
        ),
        "approved_use_cases": (
            "Application Secrets;Encryption Key Storage;"
            "Certificate Lifecycle Management"
        ),
        "prohibited_use_cases": (
            "Storing Unencrypted Credentials;Public Internet Exposure"
        ),
        "required_controls": (
            "RBAC;Private Endpoint;Audit Logging;"
            "Key Rotation;Encryption"
        ),
        "nist_functions": "Govern;Protect;Detect",
        "governance_decision": "Approved for Enterprise Use",
        "current_blockers": "No active blockers",
        "recommended_actions": (
            "Continue annual control review;"
            "Monitor service configuration standards"
        ),
        "action_owner": "Cloud Security",
        "target_action_date": "2027-05-20",
        "risk_acceptance_required": "No",
        "compensating_controls": "Not Required",
        "description": (
            "Centralized secrets and encryption key management "
            "for approved enterprise workloads"
        ),
    },
    {
        "service_id": "SVC-002",
        "service_name": "Amazon S3",
        "cloud_provider": "AWS",
        "category": "Storage",
        "approval_status": "Approved",
        "approved_regions": "us-east-1;us-west-2",
        "service_owner": "Cloud Platform",
        "last_review_date": "2026-01-15",
        "next_review_date": "2027-01-15",
        "ea_approval": "Approved",
        "cada_approval": "Approved",
        "risk_level": "Medium",
        "approved_capabilities": (
            "Object Storage;Encryption at Rest;"
            "Versioning;Lifecycle Management"
        ),
        "approved_use_cases": (
            "Application Storage;Backup Storage;Approved Data Lakes"
        ),
        "prohibited_use_cases": (
            "Public Buckets;Unencrypted Sensitive Data;Unsupported Regions"
        ),
        "required_controls": (
            "Encryption at Rest;Block Public Access;"
            "Versioning;Logging;Least Privilege"
        ),
        "nist_functions": "Govern;Protect;Detect",
        "governance_decision": "Approved with Standard Controls",
        "current_blockers": "No active blockers",
        "recommended_actions": (
            "Maintain encryption;"
            "Maintain public-access restrictions;"
            "Review lifecycle policies"
        ),
        "action_owner": "Cloud Platform",
        "target_action_date": "2027-01-15",
        "risk_acceptance_required": "No",
        "compensating_controls": "Not Required",
        "description": (
            "Enterprise object storage approved when standard "
            "security controls are enabled"
        ),
    },
    {
        "service_id": "SVC-003",
        "service_name": "Google BigQuery",
        "cloud_provider": "GCP",
        "category": "Analytics",
        "approval_status": "Conditional",
        "approved_regions": "us-central1",
        "service_owner": "Data Platform",
        "last_review_date": "2025-07-01",
        "next_review_date": "2026-07-01",
        "ea_approval": "Approved",
        "cada_approval": "Pending",
        "risk_level": "High",
        "approved_capabilities": (
            "Data Warehousing;SQL Analytics;"
            "Reporting;Approved Non-PII Workloads"
        ),
        "approved_use_cases": (
            "Operational Analytics;Executive Reporting;"
            "Approved Non-PII Data Processing"
        ),
        "prohibited_use_cases": (
            "Restricted PII;Student Records;Unsupported Regions"
        ),
        "required_controls": (
            "Encryption;IAM;Data Classification;"
            "Audit Logging;Data Loss Prevention"
        ),
        "nist_functions": "Govern;Protect;Detect",
        "governance_decision": (
            "Conditional Approval — Additional Review Required"
        ),
        "current_blockers": (
            "CADA approval pending;"
            "Review date expired;"
            "High-risk analytics use"
        ),
        "recommended_actions": (
            "Complete cloud architecture approval;"
            "Revalidate data classifications;"
            "Renew governance review"
        ),
        "action_owner": "Data Platform",
        "target_action_date": "2026-08-15",
        "risk_acceptance_required": "Yes",
        "compensating_controls": (
            "Restrict workloads to non-PII data;"
            "Enable enhanced logging;"
            "Limit access to approved analytics teams"
        ),
        "description": (
            "Enterprise analytics service requiring final cloud "
            "architecture approval and renewed review"
        ),
    },
    {
        "service_id": "SVC-004",
        "service_name": "Azure OpenAI Service",
        "cloud_provider": "Azure",
        "category": "AI/ML",
        "approval_status": "Under Review",
        "approved_regions": "East US 2",
        "service_owner": "AI Governance",
        "last_review_date": "2026-06-10",
        "next_review_date": "2026-12-10",
        "ea_approval": "Pending",
        "cada_approval": "Pending",
        "risk_level": "Critical",
        "approved_capabilities": (
            "Internal Prototyping;Text Summarization;Knowledge Search"
        ),
        "approved_use_cases": (
            "Internal Knowledge Search;"
            "Document Summarization;"
            "Approved Employee Productivity Use"
        ),
        "prohibited_use_cases": (
            "Student PII;Automated Employment Decisions;"
            "Financial Decisions;Unapproved Public Chatbots"
        ),
        "required_controls": (
            "Private Endpoint;RBAC;Prompt Logging;"
            "Content Filtering;Data Classification;Human Oversight"
        ),
        "nist_functions": "Govern;Protect;Detect;Respond",
        "governance_decision": (
            "Hold — Executive and Architecture Review Required"
        ),
        "current_blockers": (
            "EA approval pending;"
            "CADA approval pending;"
            "Critical risk classification;"
            "AI use-case boundaries incomplete"
        ),
        "recommended_actions": (
            "Complete architecture review;"
            "Document approved and prohibited use cases;"
            "Define AI monitoring controls;"
            "Submit for executive risk review"
        ),
        "action_owner": "AI Governance",
        "target_action_date": "2026-08-31",
        "risk_acceptance_required": "Yes",
        "compensating_controls": (
            "Limit access to pilot users;"
            "Prohibit sensitive data;"
            "Require human review;"
            "Enable prompt and response monitoring"
        ),
        "description": (
            "Generative AI service undergoing architecture security "
            "and responsible AI review"
        ),
    },
    {
        "service_id": "SVC-005",
        "service_name": "Amazon RDS",
        "cloud_provider": "AWS",
        "category": "Database",
        "approval_status": "Approved",
        "approved_regions": "us-east-1",
        "service_owner": "Database Engineering",
        "last_review_date": "2025-03-01",
        "next_review_date": "2026-03-01",
        "ea_approval": "Approved",
        "cada_approval": "Approved",
        "risk_level": "Medium",
        "approved_capabilities": (
            "Managed Relational Databases;Automated Backups;"
            "Encryption;High Availability"
        ),
        "approved_use_cases": (
            "Approved Application Databases;"
            "Development Databases;"
            "Production Relational Workloads"
        ),
        "prohibited_use_cases": (
            "Unencrypted Databases;Public Database Endpoints;"
            "Unsupported Engines"
        ),
        "required_controls": (
            "Encryption;Private Networking;"
            "Automated Backups;Audit Logging;Least Privilege"
        ),
        "nist_functions": "Govern;Protect;Recover",
        "governance_decision": (
            "Remediation Required — Governance Review Expired"
        ),
        "current_blockers": "Annual governance review expired",
        "recommended_actions": (
            "Complete annual service review;"
            "Validate database engine versions;"
            "Confirm backup and encryption standards"
        ),
        "action_owner": "Database Engineering",
        "target_action_date": "2026-08-10",
        "risk_acceptance_required": "No",
        "compensating_controls": "Not Required",
        "description": (
            "Managed relational database service approved with "
            "required security and resilience controls"
        ),
    },
    {
        "service_id": "SVC-006",
        "service_name": "Google Cloud Storage",
        "cloud_provider": "GCP",
        "category": "Storage",
        "approval_status": "Not Approved",
        "approved_regions": "europe-west1",
        "service_owner": "Cloud Platform",
        "last_review_date": "2026-02-18",
        "next_review_date": "2027-02-18",
        "ea_approval": "Approved",
        "cada_approval": "Missing",
        "risk_level": "High",
        "approved_capabilities": "No Enterprise Capabilities Approved",
        "approved_use_cases": "No Enterprise Use Cases Approved",
        "prohibited_use_cases": (
            "All Production Workloads;Sensitive Data Workloads"
        ),
        "required_controls": (
            "Encryption;IAM;Approved Region;"
            "Logging;Data Classification"
        ),
        "nist_functions": "Govern;Protect",
        "governance_decision": "Not Approved — Deployment Prohibited",
        "current_blockers": (
            "CADA approval missing;"
            "Region outside approved enterprise boundary;"
            "No enterprise capabilities approved"
        ),
        "recommended_actions": (
            "Move workload to an approved region;"
            "Complete cloud architecture review;"
            "Document business justification"
        ),
        "action_owner": "Cloud Platform",
        "target_action_date": "2026-08-20",
        "risk_acceptance_required": "Yes",
        "compensating_controls": (
            "Restrict access;"
            "Prevent production deployment;"
            "Apply temporary monitoring until relocation"
        ),
        "description": (
            "Cloud storage configuration outside the approved "
            "enterprise region and architecture boundary"
        ),
    },
]


def add_standard_service(
    service_id: str,
    service_name: str,
    cloud_provider: str,
    category: str,
    owner: str,
    capabilities: str,
    use_cases: str,
    controls: str,
    nist_functions: str,
    risk_level: str = "Medium",
    approval_status: str = "Approved",
    next_review_date: str = "2027-04-01",
) -> None:
    """Add a standard approved service to the synthetic catalog."""

    SERVICES.append(
        {
            "service_id": service_id,
            "service_name": service_name,
            "cloud_provider": cloud_provider,
            "category": category,
            "approval_status": approval_status,
            "approved_regions": (
                "East US;West US 2"
                if cloud_provider == "Azure"
                else (
                    "us-east-1;us-west-2"
                    if cloud_provider == "AWS"
                    else "us-central1;us-east1"
                )
            ),
            "service_owner": owner,
            "last_review_date": "2026-04-01",
            "next_review_date": next_review_date,
            "ea_approval": "Approved",
            "cada_approval": "Approved",
            "risk_level": risk_level,
            "approved_capabilities": capabilities,
            "approved_use_cases": use_cases,
            "prohibited_use_cases": (
                "Public Exposure;"
                "Unencrypted Sensitive Data;"
                "Unsupported Regions"
            ),
            "required_controls": controls,
            "nist_functions": nist_functions,
            "governance_decision": "Approved with Standard Controls",
            "current_blockers": "No active blockers",
            "recommended_actions": (
                "Maintain required controls;"
                "Complete annual governance review"
            ),
            "action_owner": owner,
            "target_action_date": next_review_date,
            "risk_acceptance_required": "No",
            "compensating_controls": "Not Required",
            "description": (
                f"{service_name} is approved for documented enterprise "
                f"use cases when required controls are implemented"
            ),
        }
    )


add_standard_service(
    "SVC-007",
    "Azure SQL Database",
    "Azure",
    "Database",
    "Database Engineering",
    "Managed SQL Database;Automated Backups;Encryption;High Availability",
    "Business Applications;Approved Production Databases",
    "Private Endpoint;Encryption;Audit Logging;Least Privilege;Backups",
    "Govern;Protect;Recover",
)

add_standard_service(
    "SVC-008",
    "Azure Functions",
    "Azure",
    "Compute",
    "Cloud Engineering",
    "Serverless Compute;Event Processing;API Integration",
    "Automation;Event-Driven Applications;Approved APIs",
    "Managed Identity;Private Endpoint;Logging;Secrets Management",
    "Govern;Protect;Detect",
)

add_standard_service(
    "SVC-009",
    "Azure Kubernetes Service",
    "Azure",
    "Containers",
    "Container Platform",
    "Container Orchestration;Autoscaling;Private Clusters",
    "Approved Container Workloads;Internal Application Platforms",
    "Private Cluster;RBAC;Image Scanning;Logging;Network Policies",
    "Govern;Protect;Detect;Respond",
    risk_level="High",
)

add_standard_service(
    "SVC-010",
    "Microsoft Defender for Cloud",
    "Azure",
    "Security",
    "Security Operations",
    "Cloud Security Posture;Threat Detection;Compliance Monitoring",
    "Security Monitoring;Configuration Assessment;Risk Reporting",
    "Logging;Alerting;RBAC;Continuous Monitoring",
    "Govern;Identify;Protect;Detect;Respond",
    risk_level="Low",
)

add_standard_service(
    "SVC-011",
    "Azure Monitor",
    "Azure",
    "Monitoring",
    "Observability",
    "Application Monitoring;Log Analytics;Alerting",
    "Operational Monitoring;Security Telemetry;Performance Reporting",
    "RBAC;Log Retention;Alerting;Data Classification",
    "Detect;Respond",
)

add_standard_service(
    "SVC-012",
    "Azure Blob Storage",
    "Azure",
    "Storage",
    "Cloud Platform",
    "Object Storage;Archiving;Lifecycle Management",
    "Application Storage;Approved Backups;Document Storage",
    "Encryption;Private Endpoint;Logging;Least Privilege",
    "Govern;Protect;Detect",
)

add_standard_service(
    "SVC-013",
    "Amazon EC2",
    "AWS",
    "Compute",
    "Cloud Engineering",
    "Virtual Machines;Autoscaling;Approved Operating Systems",
    "Enterprise Applications;Approved Compute Workloads",
    "Encryption;Systems Manager;Logging;Private Networking;Patching",
    "Govern;Protect;Detect",
)

add_standard_service(
    "SVC-014",
    "AWS Lambda",
    "AWS",
    "Compute",
    "Cloud Engineering",
    "Serverless Compute;Event Processing;Automation",
    "Automation;Data Processing;Approved API Workloads",
    "IAM Roles;Logging;Encryption;Secrets Management",
    "Govern;Protect;Detect",
)

add_standard_service(
    "SVC-015",
    "AWS Identity and Access Management",
    "AWS",
    "Identity",
    "Identity Security",
    "Identity Management;Role Management;Policy Enforcement",
    "Workforce Access;Service Access;Least-Privilege Administration",
    "MFA;Least Privilege;Logging;Access Reviews;Separation of Duties",
    "Govern;Protect;Detect",
    risk_level="High",
)

add_standard_service(
    "SVC-016",
    "Amazon EKS",
    "AWS",
    "Containers",
    "Container Platform",
    "Container Orchestration;Managed Kubernetes;Autoscaling",
    "Approved Container Platforms;Application Modernization",
    "Private Endpoint;RBAC;Image Scanning;Logging;Network Policies",
    "Govern;Protect;Detect;Respond",
    risk_level="High",
)

add_standard_service(
    "SVC-017",
    "Amazon CloudWatch",
    "AWS",
    "Monitoring",
    "Observability",
    "Metrics;Logging;Alerting;Operational Dashboards",
    "Security Monitoring;Performance Monitoring;Incident Detection",
    "Log Retention;Encryption;RBAC;Alerting",
    "Detect;Respond",
)

add_standard_service(
    "SVC-018",
    "AWS Secrets Manager",
    "AWS",
    "Security",
    "Cloud Security",
    "Secrets Management;Credential Rotation;Encryption",
    "Application Secrets;Database Credentials;API Credentials",
    "Encryption;Least Privilege;Rotation;Logging",
    "Govern;Protect;Detect",
    risk_level="Low",
)

add_standard_service(
    "SVC-019",
    "Google Compute Engine",
    "GCP",
    "Compute",
    "Cloud Engineering",
    "Virtual Machines;Autoscaling;Approved Machine Images",
    "Enterprise Applications;Approved Compute Workloads",
    "Encryption;Private Networking;Logging;Patching;IAM",
    "Govern;Protect;Detect",
)

add_standard_service(
    "SVC-020",
    "Google Kubernetes Engine",
    "GCP",
    "Containers",
    "Container Platform",
    "Container Orchestration;Managed Kubernetes;Autoscaling",
    "Approved Container Platforms;Application Modernization",
    "Private Cluster;IAM;Image Scanning;Logging;Network Policies",
    "Govern;Protect;Detect;Respond",
    risk_level="High",
)

add_standard_service(
    "SVC-021",
    "Google Cloud SQL",
    "GCP",
    "Database",
    "Database Engineering",
    "Managed SQL Database;Backups;Encryption;High Availability",
    "Approved Application Databases;Production Databases",
    "Private IP;Encryption;Audit Logging;Backups;Least Privilege",
    "Govern;Protect;Recover",
)

add_standard_service(
    "SVC-022",
    "Google Secret Manager",
    "GCP",
    "Security",
    "Cloud Security",
    "Secrets Management;Versioning;Encryption",
    "Application Secrets;API Credentials;Service Credentials",
    "IAM;Encryption;Rotation;Audit Logging",
    "Govern;Protect;Detect",
    risk_level="Low",
)

add_standard_service(
    "SVC-023",
    "Google Cloud Logging",
    "GCP",
    "Monitoring",
    "Observability",
    "Centralized Logging;Alerting;Security Telemetry",
    "Operational Monitoring;Security Monitoring;Audit Reporting",
    "Log Retention;Encryption;IAM;Alerting",
    "Detect;Respond",
)

add_standard_service(
    "SVC-024",
    "Google Cloud Functions",
    "GCP",
    "Compute",
    "Cloud Engineering",
    "Serverless Compute;Event Processing;Automation",
    "Automation;Approved APIs;Data Processing",
    "IAM;Encryption;Logging;Secrets Management",
    "Govern;Protect;Detect",
)


def main() -> None:
    """Generate the synthetic enterprise service inventory."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = pd.DataFrame(SERVICES)

    dataframe.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        f"Created {len(dataframe)} synthetic service records at:"
    )
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()