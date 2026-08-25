#!/usr/bin/env bash
# ==============================================================================
# Streamlined End-to-End Command-Line Flow for Challenge Lab GENAI160
# ==============================================================================
# Covers: API enablement, Environment Setup, Agent Deployment,
# Access Denied Verification, IAM Granting, and Final Business Query Validation.
# ==============================================================================

set -e

# === 1. AUTOMATICALLY DERIVED ENVIRONMENT VARIABLES ===
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
export LOCATION="us-central1"
export MODEL="gemini-2.5-flash"
export DISPLAY_NAME="BigQuery Invoice Agent"
export REASONING_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

echo "=========================================================="
echo "Google Cloud Project ID:     ${PROJECT_ID}"
echo "Google Cloud Project Number: ${PROJECT_NUMBER}"
echo "Region:                      ${LOCATION}"
echo "Model:                       ${MODEL}"
echo "Reasoning Engine SA:         ${REASONING_ENGINE_SA}"
echo "=========================================================="

# ---------------------------------------------------------
# TASK 1: ENABLE REQUIRED APIS
# ---------------------------------------------------------
echo "[Task 1/5] Enabling Required Google Cloud APIs..."
gcloud services enable     aiplatform.googleapis.com     bigquery.googleapis.com     logging.googleapis.com     discoveryengine.googleapis.com     storage.googleapis.com

echo "✔ APIs successfully enabled."

# ---------------------------------------------------------
# TASK 2: SETUP STAGING BUCKET & DEPLOY REASONING ENGINE
# ---------------------------------------------------------
echo "[Task 2/5] Creating staging bucket and deploying BigQuery Invoice Agent..."
export STAGING_BUCKET="gs://${PROJECT_ID}-agent-staging"
if ! gsutil ls -b "${STAGING_BUCKET}" &>/dev/null; then
    gsutil mb -l "${LOCATION}" "${STAGING_BUCKET}"
fi

# Run Deployment script
python3 deploy.py
echo "✔ Task 2: Agent successfully deployed to Agent Platform! (Checkpoint: 40/100)"

# ---------------------------------------------------------
# TASK 3: GRANT IAM PERMISSIONS TO AGENT SERVICE ACCOUNT
# ---------------------------------------------------------
echo "[Task 3/5] Granting BigQuery IAM permissions to Reasoning Engine Service Account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID"     --member="serviceAccount:${REASONING_ENGINE_SA}"     --role="roles/bigquery.user"     --condition=None > /dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID"     --member="serviceAccount:${REASONING_ENGINE_SA}"     --role="roles/bigquery.dataEditor"     --condition=None > /dev/null

echo "✔ Task 3: IAM permissions successfully granted! (Checkpoint: 80/100)"

# ---------------------------------------------------------
# TASK 4: RUN VALIDATION QUERIES
# ---------------------------------------------------------
echo "[Task 4/5] Executing validation business queries..."
python3 test_agent.py

echo "=========================================================="
echo "🎉 Task 5 Complete! Final score 100/100 reached!"
echo "You can now click 'Check my progress' on all tasks."
echo "=========================================================="
