# Granular Step-by-Step Instruction Guide: Govern Agent Access with Gemini Enterprise & Agent Platform

> **Challenge Lab Reference:** `GENAI160 / Lab ID 631982 / Course Template 1749`  
> **Lab Guide Link:** [Govern Agent Access with Gemini Enterprise & Agent Platform: Challenge Lab (Lab 631982)](https://partner.skills.google/course_templates/1749/labs/631982)  
> **Target Track:** Google Cloud Agent Development Kit (ADK) & Vertex AI Agent Platform  
> **Goal:** Deploy an enterprise BigQuery invoice agent with isolated **Agent Identity**, enforce Zero-Trust access boundaries, grant least-privilege IAM permissions, and achieve a **100/100 score**.

---

## 🎯 Lab Checkpoints & Scoring Roadmap

| Task | Objective | Checkpoint | Points | Verification Method |
| :---: | :--- | :--- | :---: | :--- |
| **Task 1** | Enable APIs, Setup Staging Bucket & Seed Dataset | Environment Setup | — | `gcloud services enable` & `bq load` |
| **Task 2** | Deploy Agent with `types.IdentityType.AGENT_IDENTITY` | **Checkpoint 1** | **40 / 100** | `python3 deploy.py` |
| **Task 3** | Validate Initial Access Controls (Verify Access Denied) | Security Verification | — | `python3 test_unprivileged.py` |
| **Task 4** | Grant Least-Privilege IAM Roles to Agent Principal | **Checkpoint 2** | **80 / 100** | `gcloud projects add-iam-policy-binding` |
| **Task 5** | Execute Business Queries & Verify Final Operation | **Checkpoint 3** | **100 / 100** | `python3 test_agent.py` |

---

## 📋 Task 1: Enable APIs & Set Up Environment

### Step 1.1: Derive and Export Environment Variables in Cloud Shell
Open the Google Cloud Shell terminal in your lab environment and run the following command to automatically detect and export your dynamic project attributes:

```bash
# Export active project ID and numerical project number
export PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
export PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null)
export LOCATION="us-central1"
export MODEL="gemini-2.5-flash"
export DISPLAY_NAME="BigQuery Invoice Agent"
export STAGING_BUCKET="gs://${PROJECT_ID}-bucket"
export REASONING_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

# Echo confirmation banner
echo "=========================================================="
echo "Project ID:                 ${PROJECT_ID}"
echo "Project Number:             ${PROJECT_NUMBER}"
echo "Region:                     ${LOCATION}"
echo "Model:                      ${MODEL}"
echo "Display Name:               ${DISPLAY_NAME}"
echo "Staging Bucket:             ${STAGING_BUCKET}"
echo "Reasoning Engine Principal: ${REASONING_ENGINE_SA}"
echo "=========================================================="
```

---

### Step 1.2: Enable Google Cloud Services
Enable all required APIs for Vertex AI Agent Engines, BigQuery, Cloud Logging, Discovery Engine, and Cloud Storage:

```bash
gcloud services enable \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    logging.googleapis.com \
    discoveryengine.googleapis.com \
    storage.googleapis.com \
    storage-component.googleapis.com \
    --project "${PROJECT_ID}"
```

---

### Step 1.3: Provision the Cloud Storage Staging Bucket
Vertex AI Agent Engines require a regional Cloud Storage bucket to stage pickled agent code artifacts:

```bash
if ! gsutil ls -b "${STAGING_BUCKET}" &>/dev/null; then
    gsutil mb -l "${LOCATION}" "${STAGING_BUCKET}"
    echo "✔ Staging bucket ${STAGING_BUCKET} created."
else
    echo "✔ Staging bucket ${STAGING_BUCKET} already exists."
fi
```

---

### Step 1.4: Copy or Initialize the `bigquery_agent_installer` Directory
If your lab pre-stages the installer in your project bucket:
```bash
gcloud storage cp -r gs://${PROJECT_ID}-bucket/bigquery_agent_installer . 2>/dev/null || true
cd bigquery_agent_installer 2>/dev/null || true
```
Or if cloning from this repository:
```bash
git clone https://github.com/junyish/genai160-Govern-Agent-Access-with-Gemini-Enterprise-Agent-Platform-Challenge-Lab.git
cd genai160-Govern-Agent-Access-with-Gemini-Enterprise-Agent-Platform-Challenge-Lab
```

---

### Step 1.5: Seed BigQuery Dataset & Invoices Table
Create the BigQuery dataset `pool_data` and populate `pool_data.invoices` with historical billing records from `past_invoices.csv`:

```bash
# 1. Create dataset
bq --project_id="${PROJECT_ID}" --location=US mk --force --dataset \
  --description "Cymbal Pools vendor invoices." "${PROJECT_ID}:pool_data"

# 2. Load CSV records into invoices table
bq --project_id="${PROJECT_ID}" --location=US load \
  --source_format=CSV --autodetect --skip_leading_rows=1 \
  --replace \
  "${PROJECT_ID}:pool_data.invoices" ./past_invoices.csv
```

**Verification:** Verify the table was created and loaded:
```bash
bq query --use_legacy_sql=false \
  "SELECT count(*) as total_invoices FROM \`${PROJECT_ID}.pool_data.invoices\`"
```
*Expected Output:* `total_invoices: 15`

---

### Step 1.6: Initialize Python Virtual Environment & Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 📋 Task 2: Configure & Deploy the Agent with `AGENT_IDENTITY`

### Step 2.1: Write the `.env` Configuration File
Generate the `.env` file in the working directory and inside `bigquery_agent/`:

```bash
cat << EOF > .env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
GOOGLE_CLOUD_LOCATION=${LOCATION}
MODEL=${MODEL}
STAGING_BUCKET=${STAGING_BUCKET}
DISPLAY_NAME="${DISPLAY_NAME}"
EOF

cp .env bigquery_agent/.env
```

---

### Step 2.2: Configure `deploy.py` with `types.IdentityType.AGENT_IDENTITY`

> [!IMPORTANT]
> **Lab Instruction Requirement:** *`IDENTITY_TYPE: Replace the placeholder with the appropriate value from types.IdentityType to deploy the agent using an Agent Identity.`*  
> The required value is `types.IdentityType.AGENT_IDENTITY`.

Ensure `deploy.py` contains:
```python
# deploy.py snippet
from vertexai._genai import types

IDENTITY_TYPE = types.IdentityType.AGENT_IDENTITY

config = {
    "display_name": DISPLAY_NAME,
    "identity_type": IDENTITY_TYPE,
    "staging_bucket": STAGING_BUCKET,
    "python_version": "3.12",
    "requirements": requirements,
    "extra_packages": ["./bigquery_agent"],
    "env_vars": {
        "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
        "GOOGLE_CLOUD_LOCATION": LOCATION,
        "MODEL": MODEL_VERSION,
        "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
    },
}
```

---

### 💡 Exact Code Diffs & Improvements in `deploy.py` (Task 2 / 2.1)

Below is the side-by-side comparison between the lab template placeholder and our production-improved `deploy.py`:

```diff
- # Placeholder in starter code:
- IDENTITY_TYPE = ... # REPLACE WITH types.IdentityType
- STAGING_BUCKET = "gs://qwiklabs-gcp-01-22c08ca0a932-bucket"

+ # Production Improved Implementation:
+ from vertexai._genai import types
+ IDENTITY_TYPE = types.IdentityType.AGENT_IDENTITY
+ STAGING_BUCKET = os.environ.get("STAGING_BUCKET", f"gs://{project}-bucket")
+
+ config = {
+     "display_name": DISPLAY_NAME,
+     "identity_type": IDENTITY_TYPE,
+     "staging_bucket": STAGING_BUCKET,
+     "python_version": "3.12",
+     "requirements": requirements,
+     "extra_packages": [f"./{AGENT_PACKAGE}"],
+     "env_vars": {
+         "GOOGLE_GENAI_USE_VERTEXAI": os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "TRUE"),
+         "GOOGLE_CLOUD_LOCATION": location,
+         "MODEL": os.environ.get("MODEL", MODEL_VERSION),
+         "GOOGLE_CLOUD_PROJECT": project,
+     },
+ }
+
+ remote_agent = client.agent_engines.create(agent=local_agent, config=config)
+ with open("deployed_agent_resource.txt", "w") as f:
+     f.write(resource_name_str.strip() + "\n")
```

### Step 2.3: Execute the Deployment
Launch the deployment to Vertex AI Agent Platform:

```bash
python3 deploy.py
```

**Expected Deployment Log Output:**
```text
Initializing Vertex AI SDK for project 'qwiklabs-gcp-...' in location 'us-central1'...
Deploying 'bigquery_agent' as 'BigQuery Invoice Agent' to Agent Runtime with Agent Identity (IdentityType.AGENT_IDENTITY)...
This typically takes 3-7 minutes.

============================================================
🎉 Agent Deployed Successfully!
Resource Name: projects/1234567890/locations/us-central1/reasoningEngines/1122334455667788
============================================================
Saved resource name to 'deployed_agent_resource.txt'
```

---

### 🎯 Checkpoint 1 (Score: 40 / 100)
1. Navigate to the lab browser window.
2. Under **Task 2**, click **Check my progress**.
3. Verify your score updates from **0/100 -> 40/100**.

---

## 📋 Task 3: Validate Initial Access Controls (Zero-Trust Baseline Check)

Under Google Cloud's Zero-Trust model, an agent deployed with **Agent Identity** has **zero default IAM permissions**. In this task, we verify that the unprivileged agent cannot read BigQuery data.

---

### Step 3.1: Execute Unprivileged Query Against Reasoning Engine
Run the `test_unprivileged.py` script:

```bash
python3 test_unprivileged.py
```

---

### Step 3.2: Verify Expected `403 Forbidden` / Access Denied Error
**Observed Terminal Output:**
```text
Connecting to Reasoning Engine: projects/1234567890/locations/us-central1/reasoningEngines/1122334455667788...
Executing test query PRIOR to IAM role binding (Task 3)...

========================================================
✔ Expected 403 Forbidden / Access Denied Encountered:
========================================================
403 Access Denied: BigQuery BigQuery: Permission 'bigquery.jobs.create' denied on project ...

This confirms that the agent runtime is securely quarantined under Zero-Trust!
```

---

## 📋 Task 4: Grant Least-Privilege IAM Roles to Agent Principal

Now we grant the agent identity the exact two IAM roles required to run query jobs and read the billing dataset.

---

### Step 4.1: Derive the Agent Principal Service Account
The Reasoning Engine service agent format is:
```bash
export REASONING_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
echo "Target Service Principal: ${REASONING_ENGINE_SA}"
```

---

### Step 4.2: Grant `roles/bigquery.user` (Job Execution & Allocation)
```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${REASONING_ENGINE_SA}" \
    --role="roles/bigquery.user" \
    --condition=None
```

---

### Step 4.3: Grant `roles/bigquery.dataEditor` (Dataset & Table Read/Write)
```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${REASONING_ENGINE_SA}" \
    --role="roles/bigquery.dataEditor" \
    --condition=None
```

---

### Step 4.4: Verify IAM Policy Bindings
```bash
gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:${REASONING_ENGINE_SA}"
```
*Expected Output:*
```text
ROLE
roles/bigquery.dataEditor
roles/bigquery.user
```

---

### 🎯 Checkpoint 2 (Score: 80 / 100)
1. Navigate to the lab browser window.
2. Under **Task 3 / Task 4**, click **Check my progress**.
3. Verify your score updates from **40/100 -> 80/100**.

---

## 📋 Task 5: Execute Business Queries & Verify Final Operation

In this final task, we send the required business analytical queries to the agent to verify end-to-end data grounding.

---

### Step 5.1: Run the Automated Validation Test Suite
```bash
python3 test_agent.py
```

---

### Step 5.2: Lab Business Queries & Expected Answers

#### Query 1: Schema Discovery
* **Prompt:** `"What is the schema of the invoices table?"`
* **Agent Output:** Lists table columns:
  - `invoice_date (DATE)`
  - `date_processed (DATE)`
  - `invoice_id (STRING)`
  - `vendor_name (STRING)`
  - `invoice_total (FLOAT)`
  - `payment_status (STRING)`

#### Query 2: Date Aggregation & Historical Total
* **Prompt:** `"What was the total sum of the invoice totals that arrived in April 2026?"`
* **Generated SQL:** `SELECT SUM(invoice_total) FROM \`pool_data.invoices\` WHERE EXTRACT(YEAR FROM invoice_date) = 2026 AND EXTRACT(MONTH FROM invoice_date) = 4`
* **Agent Output:** **`$7,672.85`**

#### Query 3: Conditional Status Filtering
* **Prompt:** `"What invoices are not paid? What is the total number of unpaid invoices?"`
* **Generated SQL:** `SELECT invoice_id, vendor_name, invoice_total FROM \`pool_data.invoices\` WHERE payment_status = 'UNPAID'`
* **Agent Output:** Lists the unpaid invoices and confirms the total count is **`6`**.

---

### 🎯 Checkpoint 3 (Final Score: 100 / 100) 🎉
1. In the lab guide, click **Check my progress** on **Task 5**.
2. Confirm your total score is **100 / 100**!

---

## ⚡ Fast-Track All-in-One CLI Command

For instant zero-click completion, run the automated runner script:

```bash
./streamlined_run_all.sh
```

---

## 🛠️ Quick Troubleshooting Guide

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `AttributeError: module 'vertexai._genai.types' has no attribute 'IdentityType'` | Outdated vertexai library in environment. | Run `pip install --upgrade "google-cloud-aiplatform[agent_engines]>=1.157.0"`. |
| Query still returns `403 Forbidden` after Task 4 | IAM propagation delay across GCP regions. | Wait 10-15 seconds for IAM policy sync and re-run `python3 test_agent.py`. |
| `Dataset pool_data not found` | BigQuery dataset was not initialized in US location. | Run `bq --location=US mk --force --dataset ${PROJECT_ID}:pool_data`. |
| `Bucket not found during deploy` | Staging bucket does not exist. | Run `gsutil mb -l us-central1 gs://${PROJECT_ID}-bucket`. |
