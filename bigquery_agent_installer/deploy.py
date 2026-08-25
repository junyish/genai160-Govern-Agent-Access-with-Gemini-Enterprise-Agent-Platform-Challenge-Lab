#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Deploy ONLY the bigquery_agent to Agent Runtime with an Agent Identity.

The deployed agent is given a unique Agent Identity (a SPIFFE-based principal)
instead of sharing a service account. That principal starts with NO access to
your data, which is why BigQuery calls are denied until you grant it the
roles/bigquery.user and roles/bigquery.dataEditor roles (see Task 3 & 4).
"""

import os
import sys
from dotenv import load_dotenv

import vertexai
from vertexai._genai import types

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
DISPLAY_NAME = os.getenv("DISPLAY_NAME", "BigQuery Invoice Agent")
MODEL_VERSION = os.getenv("MODEL", "gemini-2.5-flash")

if not PROJECT_ID:
    sys.exit("ERROR: GOOGLE_CLOUD_PROJECT is not set. Run: gcloud config set project <PROJECT_ID>")

STAGING_BUCKET = os.getenv("STAGING_BUCKET", f"gs://{PROJECT_ID}-bucket")
AGENT_PACKAGE = "bigquery_agent"

# ==============================================================================
# IDENTITY_TYPE: Deploy using dedicated Agent Identity (Zero-Trust)
# ==============================================================================
IDENTITY_TYPE = types.IdentityType.AGENT_IDENTITY

# Import the root_agent object from the bigquery_agent package
from bigquery_agent.agent import root_agent as local_agent

# Read the agent's deployment requirements from its requirements.txt
req_path = os.path.join(AGENT_PACKAGE, "requirements.txt")
if os.path.exists(req_path):
    with open(req_path) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = [
        "google-adk==2.2.0",
        "google-genai==2.8.0",
        "google-cloud-aiplatform[agent_engines]==1.157.0",
        "cloudpickle==3.1.2",
        "google-cloud-bigquery==3.41.0",
        "google-auth==2.53.0",
        "google-cloud-logging",
        "python-dotenv",
    ]

print(f"Initializing Vertex AI SDK for project '{PROJECT_ID}' in location '{LOCATION}'...")
vertexai.init(project=PROJECT_ID, location=LOCATION)
client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

config = {
    "display_name": DISPLAY_NAME,
    "identity_type": [IDENTITY_TYPE],
    "staging_bucket": STAGING_BUCKET,
    "python_version": "3.12",
    "requirements": requirements,
    "extra_packages": [f"./{AGENT_PACKAGE}"],
    "env_vars": {
        "GOOGLE_GENAI_USE_VERTEXAI": os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "TRUE"),
        "GOOGLE_CLOUD_LOCATION": LOCATION,
        "MODEL": MODEL_VERSION,
        "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
    },
}

print(f"Deploying '{AGENT_PACKAGE}' as '{DISPLAY_NAME}' to Agent Runtime with Agent Identity ({IDENTITY_TYPE})...")
print("This typically takes 3-7 minutes.")

try:
    remote_agent = client.agent_engines.create(agent=local_agent, config=config)
    res_name = getattr(remote_agent, "api_resource", None)
    res_name = getattr(res_name, "name", str(remote_agent))
except Exception as e:
    print(f"client.agent_engines.create failed ({e}). Attempting fallback with reasoning_engines.ReasoningEngine.create...")
    from vertexai.preview import reasoning_engines
    remote_agent = reasoning_engines.ReasoningEngine.create(
        reasoning_engines.AdkApp(agent=local_agent),
        requirements=requirements,
        display_name=DISPLAY_NAME,
        extra_packages=[f"./{AGENT_PACKAGE}"],
    )
    res_name = remote_agent.resource_name

print("\n" + "=" * 60)
print("🎉 Agent Deployed Successfully!")
print(f"Resource Name: {res_name}")
print("=" * 60)

with open("deployed_agent_resource.txt", "w") as f:
    f.write(str(res_name).strip() + "\n")
print("Saved resource name to 'deployed_agent_resource.txt'\n")
