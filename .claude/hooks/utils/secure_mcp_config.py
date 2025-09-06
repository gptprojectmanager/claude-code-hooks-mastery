#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "google-cloud-secret-manager",
# ]
# ///

"""
Secure MCP Configuration Generator
=================================

This utility generates MCP server configurations that use Google Secret Manager
instead of hardcoded API keys.
"""

import json
import os
import sys
from pathlib import Path
from secret_manager_loader import SecretManagerLoader

def generate_secure_mcp_config():
    """Generate secure MCP configuration using Secret Manager"""
    
    loader = SecretManagerLoader()
    
    # Get API keys from Secret Manager
    firecrawl_key = loader.get_secret('firecrawl-api-key', 'FIRECRAWL_API_KEY')
    
    if not firecrawl_key:
        print("❌ Error: Could not retrieve Firecrawl API key")
        sys.exit(1)
    
    # Create secure configuration
    secure_config = {
        "mcpServers": {
            "paper-search-mcp": {
                "command": "python3",
                "args": ["-m", "paper_search_mcp.server"],
                "env": {}
            },
            "papers-with-code-mcp": {
                "command": "python3",
                "args": ["-m", "papers_with_code_mcp"],
                "env": {}
            },
            "firecrawl-mcp": {
                "command": "npx",
                "args": ["firecrawl-mcp"],
                "env": {
                    "FIRECRAWL_API_KEY": firecrawl_key
                }
            }
        }
    }
    
    return secure_config

def update_settings_file():
    """Update the settings.json file with secure configuration"""
    settings_path = Path("/Users/sam/claude-code-hooks-mastery/.claude/settings.json")
    
    # Read current settings
    with open(settings_path, 'r') as f:
        current_settings = json.load(f)
    
    # Generate secure MCP config
    secure_mcp_config = generate_secure_mcp_config()
    
    # Update only the MCP servers section
    current_settings["mcpServers"] = secure_mcp_config["mcpServers"]
    
    # Create backup first
    backup_path = settings_path.with_suffix('.json.backup')
    with open(backup_path, 'w') as f:
        json.dump(current_settings, f, indent=2)
    
    print(f"✅ Created backup at {backup_path}")
    
    # Write updated settings
    with open(settings_path, 'w') as f:
        json.dump(current_settings, f, indent=2)
    
    print(f"✅ Updated settings file with Secret Manager integration")
    
    return settings_path

def main():
    """Main function"""
    print("🔐 Generating Secure MCP Configuration...")
    
    try:
        updated_path = update_settings_file()
        print(f"✅ Successfully updated: {updated_path}")
        
        # Verify the configuration
        with open(updated_path, 'r') as f:
            config = json.load(f)
        
        firecrawl_config = config.get("mcpServers", {}).get("firecrawl-mcp", {})
        if "FIRECRAWL_API_KEY" in firecrawl_config.get("env", {}):
            print("✅ Firecrawl API key loaded from Secret Manager")
        else:
            print("❌ Firecrawl API key not found in configuration")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()