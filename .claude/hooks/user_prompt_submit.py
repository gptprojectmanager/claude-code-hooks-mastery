#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "requests",
# ]
# ///

import argparse
import json
import os
import sys
import requests
from pathlib import Path
from datetime import datetime
from utils.constants import ensure_session_log_dir

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def log_user_prompt(session_id, input_data):
    """Log user prompt to session directory."""
    log_dir = ensure_session_log_dir(session_id)
    log_file = log_dir / 'user_prompt_submit.json'
    
    if log_file.exists():
        with open(log_file, 'r') as f:
            try:
                log_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                log_data = []
    else:
        log_data = []
    
    log_data.append(input_data)
    
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)


def route_to_litellm(prompt, model_alias, command_name):
    """Routes a prompt to the local LiteLLM server."""
    litellm_url = "http://localhost:4002/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    user_content = prompt.split(maxsplit=1)[1] if len(prompt.split()) > 1 else ""

    if not user_content:
        print(f"Error: No prompt provided after {command_name} command.", file=sys.stderr)
        return

    data = {
        "model": model_alias,
        "messages": [{"role": "user", "content": user_content}],
        "stream": False
    }

    try:
        print(f"--- 💎 Calling {model_alias}... ---")
        response = requests.post(litellm_url, headers=headers, json=data, timeout=180)
        
        response_data = response.json()

        if response.status_code != 200:
            error_message = response_data.get("error", {}).get("message", response.text)
            print(f"\n--- ❌ Error from {model_alias} ---")
            print(error_message)
            print("---------------------------------\n")
            return

        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        print(f"\n--- ✅ {model_alias} Response ---")
        print(content)
        print("---------------------------\n")

    except requests.exceptions.RequestException as e:
        print(f"\nError connecting to LiteLLM server: {e}", file=sys.stderr)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--route-llm', action='store_true', help='Enable routing to LiteLLM for commands')
        args, _ = parser.parse_known_args()
        
        input_data = json.loads(sys.stdin.read())
        session_id = input_data.get('session_id', 'unknown')
        prompt = input_data.get('prompt', '').strip()
        
        log_user_prompt(session_id, input_data)

        if args.route_llm:
            if prompt.startswith('/gpro'):
                route_to_litellm(prompt, 'gemini-pro', '/gpro')
                sys.exit(0)
            elif prompt.startswith('/gflash'):
                route_to_litellm(prompt, 'gemini-flash', '/gflash')
                sys.exit(0)
        
        sys.exit(0)
        
    except Exception:
        sys.exit(0)


if __name__ == '__main__':
    main()
