#!/usr/bin/env python3
"""
Test script to verify Browser Automation Agent setup
"""

import os
import subprocess
import json

def check_mcp_servers():
    """Check if MCP servers are properly installed"""
    print("🔍 Checking MCP Server Installations")
    print("=" * 50)
    
    servers = [
        {
            "name": "Playwright MCP Server",
            "path": "/Users/sam/.npm-global/lib/node_modules/@executeautomation/playwright-mcp-server/dist/index.js"
        },
        {
            "name": "Puppeteer MCP Server", 
            "path": "/Users/sam/.npm-global/lib/node_modules/puppeteer-mcp-server/dist/index.js"
        }
    ]
    
    for server in servers:
        if os.path.exists(server["path"]):
            print(f"✅ {server['name']}: Found at {server['path']}")
        else:
            print(f"❌ {server['name']}: NOT FOUND at {server['path']}")
    
    return True

def check_claude_config():
    """Check Claude configuration for new MCP servers"""
    print(f"\n🔧 Checking Claude Configuration")
    print("=" * 50)
    
    config_path = "/Users/sam/.claude.json"
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for MCP servers in project config
        projects = config.get('projects', {})
        sam_project = projects.get('/Users/sam', {})
        mcp_servers = sam_project.get('mcpServers', {})
        
        expected_servers = ['playwright', 'puppeteer']
        for server in expected_servers:
            if server in mcp_servers:
                print(f"✅ {server.title()} MCP server configured")
            else:
                print(f"❌ {server.title()} MCP server NOT configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Claude config: {e}")
        return False

def check_agent_file():
    """Check if Browser Automation Agent file exists"""
    print(f"\n👤 Checking Browser Automation Agent")
    print("=" * 50)
    
    agent_path = "/Users/sam/claude-code-hooks-mastery/.claude/agents/browser-automation-agent.md"
    if os.path.exists(agent_path):
        print("✅ Browser Automation Agent file created")
        
        # Check content
        with open(agent_path, 'r') as f:
            content = f.read()
            if 'playwright' in content and 'puppeteer' in content:
                print("✅ Agent configured with browser automation tools")
            else:
                print("⚠️  Agent may not have proper tool configuration")
    else:
        print("❌ Browser Automation Agent file NOT FOUND")
    
    return os.path.exists(agent_path)

def check_investigation_script():
    """Check if investigation script exists"""
    print(f"\n📋 Checking Investigation Script")
    print("=" * 50)
    
    script_path = "/Users/sam/claude-code-hooks-mastery/investigate_dashboard.md"
    if os.path.exists(script_path):
        print("✅ Dashboard investigation script created")
        
        with open(script_path, 'r') as f:
            content = f.read()
            if '@browser-automation-agent' in content:
                print("✅ Script properly references Browser Automation Agent")
            else:
                print("⚠️  Script may not reference agent properly")
    else:
        print("❌ Investigation script NOT FOUND")
    
    return os.path.exists(script_path)

def main():
    print("🎭 BROWSER AUTOMATION AGENT SETUP VERIFICATION")
    print("=" * 60)
    
    checks = [
        check_mcp_servers(),
        check_claude_config(), 
        check_agent_file(),
        check_investigation_script()
    ]
    
    successful_checks = sum(checks)
    total_checks = len(checks)
    
    print(f"\n📊 SETUP VERIFICATION RESULTS")
    print("=" * 40)
    print(f"✅ Successful checks: {successful_checks}/{total_checks}")
    
    if successful_checks == total_checks:
        print("\n🎉 Browser Automation Agent setup is COMPLETE!")
        print("🎯 Ready to investigate dashboard issues")
        print("📝 Next step: Invoke @browser-automation-agent with investigate_dashboard.md")
        print("🌐 Target: http://localhost:4000 dashboard analysis")
    else:
        print(f"\n⚠️  Setup incomplete - {total_checks - successful_checks} issues found")
        print("🔧 Please resolve issues before proceeding")
    
    print(f"\n🚀 USAGE INSTRUCTIONS")
    print("=" * 40)
    print("1. Restart Claude Code to load new MCP servers")
    print("2. Use: @browser-automation-agent")
    print("3. Reference: investigate_dashboard.md")
    print("4. Target URL: http://localhost:4000")
    
    return successful_checks == total_checks

if __name__ == "__main__":
    main()