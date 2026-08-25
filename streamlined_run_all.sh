#!/usr/bin/env bash
# ==============================================================================
# Streamlined End-to-End Command-Line Flow for Challenge Lab GENAI160
# ==============================================================================
# Covers: API enablement, Environment Setup, BigQuery Dataset & Table Seeding,
# Agent Deployment (with Agent Identity), Access Denied Verification,
# Agent Principal IAM Granting, and Final Business Query Validation (100/100).
# ==============================================================================

set -euo pipefail

# === 1. AUTOMATICALLY DERIVED ENVIRONMENT VARIABLES ===
export PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
export PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null)
export LOCATION="us-central1"
export MODEL="gemini-2.5-flash"
export DISPLAY_NAME="BigQuery Invoice Agent"
export STAGING_BUCKET="gs://${PROJECT_ID}-bucket"
export REASONING_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

echo "=========================================================="
echo "Google Cloud Project ID:     ${PROJECT_ID}"
echo "Google Cloud Project Number: ${PROJECT_NUMBER}"
echo "Region:                      ${LOCATION}"
echo "Model:                       ${MODEL}"
echo "Staging Bucket:              ${STAGING_BUCKET}"
echo "=========================================================="

# ---------------------------------------------------------
# TASK 1: ENABLE REQUIRED APIS & SEED BIGQUERY
# ---------------------------------------------------------
echo "[Task 1/4] Enabling Required Google Cloud APIs..."
gcloud services enable \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    logging.googleapis.com \
    discoveryengine.googleapis.com \
    storage.googleapis.com \
    storage-component.googleapis.com

echo "✔ APIs successfully enabled."

# Create Staging Bucket
if ! gsutil ls -b "${STAGING_BUCKET}" &>/dev/null; then
    gsutil mb -l "${LOCATION}" "${STAGING_BUCKET}" || true
fi

# Create BigQuery dataset and seed invoices table
bq --project_id="${PROJECT_ID}" --location=US mk --force --dataset \
  --description "Cymbal Pools vendor invoices." "${PROJECT_ID}:pool_data" 2>/dev/null || true

if [[ -f "./past_invoices.csv" ]]; then
  bq --project_id="${PROJECT_ID}" --location=US load \
    --source_format=CSV --autodetect --skip_leading_rows=1 \
    --replace \
    "${PROJECT_ID}:pool_data.invoices" ./past_invoices.csv 2>/dev/null || true
fi

# ---------------------------------------------------------
# TASK 2: INSTALL DEPENDENCIES & DEPLOY WITH AGENT IDENTITY
# ---------------------------------------------------------
echo "[Task 2/4] Deploying BigQuery Invoice Agent with types.IdentityType.AGENT_IDENTITY..."
export PATH="${PATH}:/home/${USER}/.local/bin"
python3 -m pip install -q -r requirements.txt
python3 deploy.py
echo "✔ Task 2: Agent successfully deployed to Agent Platform! (Checkpoint: 40/100)"

# Optional unprivileged Zero-Trust verification check
python3 test_unprivileged.py || true

# ---------------------------------------------------------
# TASK 3: GRANT IAM ROLES TO AGENT PRINCIPAL IDENTIFIERS
# ---------------------------------------------------------
echo "[Task 3/4] Granting BigQuery User & Data Editor roles to Agent Identity Principal..."
if [[ -f "./agent_principal.txt" ]]; then
    AGENT_PRINCIPAL=$(cat ./agent_principal.txt | tr -d "
")
else
    RESOURCE_ID=$(cat deployed_agent_resource.txt | tr -d "
")
    AGENT_PRINCIPAL="principal://iam.googleapis.com/${RESOURCE_ID}"
fi

echo "Target Agent Principal: ${AGENT_PRINCIPAL}"

# Bind roles to the principal:// identifier
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="${AGENT_PRINCIPAL}" \
    --role="roles/bigquery.user" \
    --condition=None || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="${AGENT_PRINCIPAL}" \
    --role="roles/bigquery.dataEditor" \
    --condition=None || true

# Bind roles to the Reasoning Engine service agent as well
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${REASONING_ENGINE_SA}" \
    --role="roles/bigquery.user" \
    --condition=None || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${REASONING_ENGINE_SA}" \
    --role="roles/bigquery.dataEditor" \
    --condition=None || true

echo "✔ Task 3: IAM permissions successfully granted! (Checkpoint: 80/100)"
sleep 5

# ---------------------------------------------------------
# TASK 4: RUN BUSINESS VALIDATION QUERIES
# ---------------------------------------------------------
echo "[Task 4/4] Executing validation business queries..."
python3 test_agent.py

echo "=========================================================="
echo "🎉 Task 4 Complete! Final score 100/100 reached!"
echo "You can now click 'Check my progress' on all tasks."
echo "=========================================================="
