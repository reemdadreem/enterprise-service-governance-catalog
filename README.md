# Enterprise Service Governance Catalog

A Streamlit application that simulates a centralized operational inventory for enterprise cloud services.

## Business problem

Governance teams often lack a single place to determine:

- whether a service is approved
- which cloud and regions it supports
- who owns the service
- whether architecture and security reviews are complete
- when the service must be reviewed again
- whether duplicate or overlapping services already exist

## MVP capabilities

- Searchable service inventory
- Cloud, status, risk, and region filters
- Governance readiness rules
- Expired review detection
- Missing approval detection
- Executive KPI summary

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app/app.py
```
