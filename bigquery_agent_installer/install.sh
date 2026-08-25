#!/usr/bin/env bash
#
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License").
#
# Installer for bigquery_agent from the GENAI160 / GENAI155 lab.
#
# It provisions the single BigQuery agent and deploys it to
# Agent Runtime with its own Agent Identity:
#   1. Enables the required APIs.
#   2. Creates the gs://<project>-bucket staging bucket.
#   3. Creates the pool_data BigQuery dataset and loads the invoices table
#      from past_invoices.csv (15 historical invoices).
#   4. Installs the Python requirements and writes a .env.
#   5. Deploys the bigquery_agent (Agent Identity, denied-by-default).
#
# Usage:
#   ./install.sh                  # uses active gcloud project + us-central1
#   PROJECT_ID=my-proj REGION=us-central1 ./install.sh

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
PROJECT_NUMBER="${PROJECT_NUMBER:-$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || true)}"
REGION="${REGION:-us-central1}"
MODEL="${MODEL:-gemini-2.5-flash}"
BUCKET="gs://${PROJECT_ID}-bucket"
REASONING_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "ERROR: No project set. Run 'gcloud config set project <PROJECT_ID>' or pass PROJECT_ID=..." >&2
  exit 1
fi

cd "$(dirname "$0")"

echo "=========================================================="
echo "=== BigQuery Agent Installer (GENAI160 Challenge Lab) ==="
echo "=========================================================="
echo "Project ID:          ${PROJECT_ID}"
echo "Project Number:      ${PROJECT_NUMBER}"
echo "Region:              ${REGION}"
echo "Model:               ${MODEL}"
echo "Staging Bucket:      ${BUCKET}"
echo "Reasoning Engine SA: ${REASONING_ENGINE_SA}"
echo "=========================================================="
echo

echo "[1/5] Enabling required APIs..."
gcloud services enable \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  logging.googleapis.com \
  storage.googleapis.com \
  storage-component.googleapis.com \
  --project "${PROJECT_ID}"

echo "[2/5] Creating staging bucket ${BUCKET} (ok if it already exists)..."
gcloud storage buckets create "${BUCKET}" \
  --project "${PROJECT_ID}" --location "${REGION}" 2>/dev/null \
  || echo "  bucket already exists, continuing."

echo "[3/5] Creating pool_data dataset and loading the invoices table..."
bq --project_id="${PROJECT_ID}" --location=US mk --force --dataset \
  --description "Cymbal Pools vendor invoices." "${PROJECT_ID}:pool_data" 2>/dev/null || true

if [[ -f "./past_invoices.csv" ]]; then
  bq --project_id="${PROJECT_ID}" --location=US load \
    --source_format=CSV --autodetect --skip_leading_rows=1 \
    --replace \
    "${PROJECT_ID}:pool_data.invoices" ./past_invoices.csv
  echo "  loaded past_invoices.csv into pool_data.invoices."
else
  echo "  past_invoices.csv not found locally, skipping load."
fi

echo "[4/5] Installing Python requirements and writing .env..."
export PATH="${PATH}:/home/${USER}/.local/bin"
python3 -m pip install -q -r requirements.txt

cat > .env <<EOF
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
GOOGLE_CLOUD_LOCATION=${REGION}
MODEL=${MODEL}
STAGING_BUCKET=${BUCKET}
DISPLAY_NAME="BigQuery Invoice Agent"
EOF

cp .env bigquery_agent/.env 2>/dev/null || true

echo "[5/5] Deploying the bigquery_agent (takes ~3-7 minutes)..."
python3 deploy.py

echo
echo "=========================================================="
echo "✔ Deployment Complete! (Task 2 Score: 40/100)"
echo "=========================================================="
echo "Next Step: Grant the agent identity its BigQuery roles (Task 4):"
echo "  gcloud projects add-iam-policy-binding \"${PROJECT_ID}\" \\"
echo "    --member=\"serviceAccount:${REASONING_ENGINE_SA}\" \\"
echo "    --role=\"roles/bigquery.user\""
echo ""
echo "  gcloud projects add-iam-policy-binding \"${PROJECT_ID}\" \\"
echo "    --member=\"serviceAccount:${REASONING_ENGINE_SA}\" \\"
echo "    --role=\"roles/bigquery.dataEditor\""
echo "=========================================================="
