#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "google-cloud-secret-manager",
# ]
# ///

import sys
from google.cloud import secretmanager

def get_gemini_api_key():
    """Retrieve Gemini API key from Google Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = "custom-mix-460500-g9"
        secret_name = f"projects/{project_id}/secrets/gemini-api-key/versions/latest"
        
        response = client.access_secret_version(request={"name": secret_name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error retrieving API key: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    key = get_gemini_api_key()
    if key:
        print(key)
    else:
        exit(1)