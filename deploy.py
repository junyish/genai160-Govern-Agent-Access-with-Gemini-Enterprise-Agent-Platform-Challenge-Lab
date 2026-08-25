#!/usr/bin/env python3
# Copyright 2025 Google LLC
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

"""
Deployment script for BigQuery Invoice Agent on Vertex AI Agent Engine.
"""

import os
from dotenv import load_dotenv
import vertexai
from vertexai import types
from vertexai.preview import reasoning_engines
from invoice_agent.agent import root_agent

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")
DISPLAY_NAME = os.getenv("DISPLAY_NAME", "BigQuery Invoice Agent")

# ==============================================================================
# IDENTITY_TYPE: Deploy the agent using dedicated Agent Identity
# ==============================================================================
try:
    IDENTITY_TYPE = types.IdentityType.AGENT_IDENTITY
except AttributeError:
    IDENTITY_TYPE = "AGENT_IDENTITY"

if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required.")

print(f"Initializing Vertex AI SDK for project: {PROJECT_ID}, location: {LOCATION}...")
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

print(f"Deploying '{DISPLAY_NAME}' to Vertex AI Agent Engines with IDENTITY_TYPE={IDENTITY_TYPE}...")
remote_agent = reasoning_engines.ReasoningEngine.create(
    reasoning_engines.AdkApp(agent=root_agent),
    requirements=[
        "google-cloud-aiplatform[agent_engines,adk]==1.156.0",
        "cloudpickle",
        "google-cloud-bigquery",
        "google-auth",
        "pydantic",
        "python-dotenv",
        "google-cloud-logging",
    ],
    display_name=DISPLAY_NAME,
    identity_type=IDENTITY_TYPE,
    description="Agent to query and govern BigQuery invoice and billing data.",
    extra_packages=["./invoice_agent"],
)

print("\n" + "=" * 60)
print("🎉 Deployment Successful!")
print(f"Reasoning Engine Display Name:   {remote_agent.display_name}")
print(f"Reasoning Engine Resource Name: {remote_agent.resource_name}")
print("=" * 60 + "\n")

# Save resource name to local file for test scripts and automation
with open("deployed_agent_resource.txt", "w") as f:
    f.write(remote_agent.resource_name.strip() + "\n")
print("Saved resource name to 'deployed_agent_resource.txt'")
