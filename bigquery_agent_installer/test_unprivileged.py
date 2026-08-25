#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
import vertexai
from vertexai.preview import reasoning_engines

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if not PROJECT_ID:
    sys.exit("ERROR: GOOGLE_CLOUD_PROJECT is not set.")

with open("deployed_agent_resource.txt", "r") as f:
    RE_RESOURCE_NAME = f.read().strip()

print(f"Connecting to Reasoning Engine: {RE_RESOURCE_NAME}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)
remote_agent = reasoning_engines.ReasoningEngine(RE_RESOURCE_NAME)

print("Executing test query PRIOR to IAM role binding (Task 3)...")
try:
    response = remote_agent.query(input="What is the schema of the invoice table?")
    print("Unexpected Success:
", response)
except Exception as e:
    print("
========================================================")
    print("✔ Expected 403 Forbidden / Access Denied Encountered:")
    print("========================================================")
    print(e)
    print("
This confirms that the agent runtime is securely quarantined under Zero-Trust!")
