#!/usr/bin/env python3
"""
Test script to interact with deployed BigQuery Invoice Agent on Vertex AI.
"""

import os
import sys
from dotenv import load_dotenv
import vertexai
from vertexai.preview import reasoning_engines

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required.")

# Read deployed resource name
resource_file = "deployed_agent_resource.txt"
if os.path.exists(resource_file):
    with open(resource_file, "r") as f:
        RE_RESOURCE_NAME = f.read().strip()
else:
    RE_RESOURCE_NAME = os.getenv("REASONING_ENGINE_RESOURCE_NAME")

if not RE_RESOURCE_NAME:
    print("Error: No reasoning engine resource specified. Provide via deployed_agent_resource.txt or REASONING_ENGINE_RESOURCE_NAME.")
    sys.exit(1)

print(f"Connecting to Reasoning Engine: {RE_RESOURCE_NAME}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)
remote_agent = reasoning_engines.ReasoningEngine(RE_RESOURCE_NAME)

queries = [
    "What is the schema of the invoice table?",
    "What was the total sum of invoice totals from the second-to-last month?",
    "What invoices are not paid? What is the total number of unpaid invoices?",
]

for idx, q in enumerate(queries, 1):
    print(f"\n--- [Query {idx}] {q} ---")
    try:
        response = remote_agent.query(input=q)
        print("Agent Response:\n", response)
    except Exception as e:
        print(f"❌ Query execution error (May indicate missing IAM permissions): {e}")
