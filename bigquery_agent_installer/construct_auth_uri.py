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

"""
Helper script to construct and URL-encode the Authorization URI for
Gemini Enterprise / Agent Platform OAuth 2.0 Registration.
"""

import os

OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "YOUR_CLIENT_ID")
SCOPES = ["https://www.googleapis.com/auth/bigquery"]
REDIRECT_URI = "https://vertexaisearch.cloud.google.com/static/oauth/oauth.html"
OTHER_REQUIRED_QUERY_PARAMETERS = "include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent"

query_parameters = [
    f"client_id={OAUTH_CLIENT_ID}",
    f"redirect_uri={REDIRECT_URI}",
    OTHER_REQUIRED_QUERY_PARAMETERS
]
if SCOPES:
    scopes_substring = f"scope={'%20'.join(SCOPES)}"
    query_parameters.append(scopes_substring)

query_parameters_joined = "&".join(query_parameters)
query_parameters_to_html_encoding = (
    query_parameters_joined
    .replace(" ", "%20")
    .replace(":", "%3A")
    .replace("/", "%2F")
)

auth_uri = "https://accounts.google.com/o/oauth2/v2/auth?" + query_parameters_to_html_encoding
print("Auth URI:\n\n" + auth_uri + "\n\n")
