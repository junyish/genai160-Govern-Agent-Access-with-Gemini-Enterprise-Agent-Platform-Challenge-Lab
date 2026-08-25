# Granular Step-by-Step Instruction Guide: Govern Agent Access with Gemini Enterprise & Agent Platform

> **Challenge Lab Reference:** `GENAI160 / Lab ID 631982 / Course Template 1749`  
> **Lab Guide Link:** [Govern Agent Access with Gemini Enterprise & Agent Platform: Challenge Lab (Lab 631982)](https://partner.skills.google/course_templates/1749/labs/631982)  
> **Target Track:** Google Cloud Agent Development Kit (ADK) & Vertex AI Agent Platform  
> **Goal:** Deploy an enterprise BigQuery invoice agent with isolated **Agent Identity**, find the dedicated **Agent Principal Identifier**, grant least-privilege IAM permissions (`roles/bigquery.user` and `roles/bigquery.dataEditor`), and achieve a **100/100 score**.

---

## 🎯 Lab Tasks & Checkpoint Scoring Matrix

| Lab Task | Objective | Checkpoint Points | Verification Action |
| :---: | :--- | :---: | :--- |
| **Task 1** | Enable APIs, Create Staging Bucket & Seed BigQuery Dataset | Baseline Setup | `gcloud services enable` & `bq load` |
| **Task 2** | Configure & Deploy BigQuery Agent with `AGENT_IDENTITY` | **40 / 100** | Click **Check my progress** on Task 2 |
| **Task 3** | Find Agent Principal Identifier & Grant **BigQuery User** + **Data Editor** | **80 / 100** | Click **Check my progress** on Task 3 |
| **Task 4** | Query the Agent & Verify Grounded Business Answers | **100 / 100** | Click **Check my progress** on Task 4 |

---

## 📋 Task 1: Enable APIs, Setup Staging Bucket & Seed Dataset

### Step 1.1: Derive and Export Environment Variables in Cloud Shell
Open the Google Cloud Shell terminal in your lab environment and run the following commands:

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

### Step 1.2: Enable Required Google Cloud APIs
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
```bash
if ! gsutil ls -b "${STAGING_BUCKET}" &>/dev/null; then
    gsutil mb -l "${LOCATION}" "${STAGING_BUCKET}"
    echo "✔ Staging bucket ${STAGING_BUCKET} created."
else
    echo "✔ Staging bucket ${STAGING_BUCKET} already exists."
fi
```

---

### Step 1.4: Clone Starter Repository
```bash
git clone https://github.com/junyish/genai160-Govern-Agent-Access-with-Gemini-Enterprise-Agent-Platform-Challenge-Lab.git lab-genai160
cd lab-genai160
```

---

### Step 1.5: Seed BigQuery Dataset & Invoices Table
Create dataset `pool_data` and populate `pool_data.invoices` with 15 historical records from `past_invoices.csv`:

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

**Verification:** Check loaded record count:
```bash
bq query --use_legacy_sql=false \
  "SELECT count(*) as total_invoices FROM \`${PROJECT_ID}.pool_data.invoices\`"
```
*Expected Output:* `total_invoices: 15`

---

### Step 1.6: Install Python Dependencies
```bash
export PATH="${PATH}:/home/${USER}/.local/bin"
python3 -m pip install -q -r requirements.txt
```

---

## 📋 Task 2: Configure & Deploy the BigQuery Agent (Checkpoint: 40/100)

### Step 2.1: Write the `.env` Configuration File
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

### Step 2.2: Configure `deploy.py` with `IdentityType.AGENT_IDENTITY`
In `deploy.py`, ensure `identity_type` is configured as a scalar with `types.IdentityType.AGENT_IDENTITY`:

```python
# deploy.py snippet
from vertexai._genai import types

IDENTITY_TYPE = types.IdentityType.AGENT_IDENTITY
STAGING_BUCKET = os.environ.get("STAGING_BUCKET", f"gs://{project}-bucket")

config = {
    "display_name": DISPLAY_NAME,
    "identity_type": IDENTITY_TYPE,
    "staging_bucket": STAGING_BUCKET,
    "python_version": "3.12",
    "requirements": requirements,
    "extra_packages": [f"./{AGENT_PACKAGE}"],
    "env_vars": {
        "GOOGLE_GENAI_USE_VERTEXAI": os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "TRUE"),
        "GOOGLE_CLOUD_LOCATION": location,
        "MODEL": os.environ.get("MODEL", MODEL_VERSION),
    },
}
```

---

### Step 2.3: Execute Deployment to Agent Platform
```bash
python3 deploy.py
```

**Expected Output:**
```text
Deploying 'bigquery_agent' as 'BigQuery Invoice Agent' to Agent Runtime with an Agent Identity...
This typically takes 5-10 minutes.

============================================================
🎉 Agent Deployed Successfully!
Resource Name:            projects/1234567890/locations/us-central1/reasoningEngines/1122334455667788
Agent Identity Principal: principal://iam.googleapis.com/projects/1234567890/locations/us-central1/reasoningEngines/1122334455667788
============================================================
```

---

### 🎯 Checkpoint 1 (Score: 40 / 100)
1. In the lab guide under **Task 2**, click **Check my progress**.
2. Verify your score increases to **40 / 100**.

---

### 💡 (Optional Security Verification) Verify Access Denied
```bash
python3 test_unprivileged.py
```
*Expected Output:* `403 Forbidden / Access Denied` (confirms Zero-Trust isolation is operating as intended).

---

## 📋 Task 3: Find Agent Principal Identifier & Grant IAM Roles (Checkpoint: 80/100)

> [!IMPORTANT]
> **Lab Requirement:** Find the deployed agent's **Agent Identity Principal** and grant it two roles:
> 1. **BigQuery User** (`roles/bigquery.user`)
> 2. **BigQuery Data Editor** (`roles/bigquery.dataEditor`)

### Step 3.1: Retrieve the Agent Identity Principal Identifier

#### Method A (From Deployment Output):
The deployment script automatically saved the principal identifier to `agent_principal.txt`:
```bash
export AGENT_PRINCIPAL=$(cat agent_principal.txt | tr -d "
")
echo "Agent Principal Identifier: ${AGENT_PRINCIPAL}"
```

#### Method B (From Google Cloud Console):
1. In the Google Cloud Console, navigate to **Agent Platform** (or **Vertex AI > Agent Engines / Deployments**).
2. Click on **BigQuery Invoice Agent** under **Deployments**.
3. Under the deployment details, copy the **Agent Identity Principal** (format: `principal://agents.global.org-<ORG_ID>.system.id.goog/resources/aiplatform/projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<ID>`\n*(Example: `principal://agents.global.org-616463121992.system.id.goog/resources/aiplatform/projects/1057612962708/locations/us-central1/reasoningEngines/1703351868878487552`)*).

---

### Step 3.2: Grant BigQuery User & Data Editor Roles

#### CLI Method (Recommended):
```bash
# 1. Grant BigQuery User role to the Agent Principal
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="${AGENT_PRINCIPAL}" \
    --role="roles/bigquery.user" \
    --condition=None

# 2. Grant BigQuery Data Editor role to the Agent Principal
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="${AGENT_PRINCIPAL}" \
    --role="roles/bigquery.dataEditor" \
    --condition=None
```

*(Optional safety fallback for Reasoning Engine service agent):*
```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${REASONING_ENGINE_SA}" \
    --role="roles/bigquery.user" --condition=None || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${REASONING_ENGINE_SA}" \
    --role="roles/bigquery.dataEditor" --condition=None || true
```

#### Console UI Method:
1. Go to **IAM & Admin > IAM** in the Cloud Console.
2. Click **Grant Access** (or **Add**).
3. In **New principals**, paste your copied `${AGENT_PRINCIPAL}` string.
4. In **Select a role**, choose **BigQuery User** (`roles/bigquery.user`).
5. Click **+ Add another role**, and choose **BigQuery Data Editor** (`roles/bigquery.dataEditor`).
6. Click **Save**.

---

### Step 3.3: Verify IAM Policy Binding
```bash
gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:${AGENT_PRINCIPAL}"
```

**Expected Verification Output:**
```text
ROLE
roles/bigquery.dataEditor
roles/bigquery.user
```

---

### 🎯 Checkpoint 2 (Score: 80 / 100)
1. In the lab guide under **Task 3**, click **Check my progress**.
2. Verify your score increases to **80 / 100**.

---

## 📋 Task 4: Query the Agent & Verify Grounded Business Answers (Checkpoint: 100/100)

### Step 4.1: Run the Automated Validation Test Script
```bash
python3 test_agent.py
```

---

### Step 4.2: Lab Business Queries & Expected Answers

#### Query 1: Schema Inspection
* **Question:** `"What is the schema of the invoices table?"`
* **Result:** Returns table columns:
  - `invoice_date (DATE)`
  - `date_processed (DATE)`
  - `invoice_id (STRING)`
  - `vendor_name (STRING)`
  - `invoice_total (FLOAT)`
  - `payment_status (STRING)`

#### Query 2: Sum of Invoices in April 2026
* **Question:** `"What was the total sum of the invoice totals that arrived in April 2026?"`
* **Result:** **`$7,672.85`**

#### Query 3: Count and List of Unpaid Invoices
* **Question:** `"What invoices are not paid? What is the total number of unpaid invoices?"`
* **Result:** **`6`** unpaid invoices.

---

### 🎯 Checkpoint 3 (Final Score: 100 / 100) 🎉
1. In the lab guide under **Task 4**, click **Check my progress**.
2. Confirm your total score reaches **100 / 100**! 🏆

---

## ⚡ Instant All-in-One Shortcut Command

```bash
cd ~ && rm -rf lab-run && git clone https://github.com/junyish/genai160-Govern-Agent-Access-with-Gemini-Enterprise-Agent-Platform-Challenge-Lab.git lab-run && cd lab-run && chmod +x streamlined_run_all.sh && ./streamlined_run_all.sh
```
