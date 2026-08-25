#!/usr/bin/env python3
# Copyright 2026 Google LLC
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

if not os.path.exists("deployed_agent_resource.txt"):
    sys.exit("ERROR: deployed_agent_resource.txt not found. Run deploy.py first.")

with open("deployed_agent_resource.txt", "r") as f:
    RE_RESOURCE_NAME = f.read().strip()

print(f"Connecting to Reasoning Engine: {RE_RESOURCE_NAME}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)
remote_agent = reasoning_engines.ReasoningEngine(RE_RESOURCE_NAME)

queries = [
    "What is the schema of the invoice table?",
    "What was the total sum of invoice totals from the second-to-last month?",
    "What invoices are not paid? What is the total number of unpaid invoices?",
]

for idx, q in enumerate(queries, 1):
    print("\n" + "=" * 60)
    print(f"🧪 [Query {idx}/3] {q}")
    print("=" * 60)
    try:
        response = remote_agent.query(input=q)
        print("\n🤖 Agent Grounded Response:\n", response)
    except Exception as e:
        print(f"\n❌ Error executing query: {e}")
        sys.exit(1)

print("\n" + "=" * 60)
print("🎉 All 3 Business Queries Executed Successfully!")
print("=" * 60)
