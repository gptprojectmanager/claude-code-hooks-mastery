# Apps Directory Analysis Report

**Analysis Date**: 2025-09-04 21:05
**Task ID**: 12d447dd-8eea-4829-88be-6c57d8238e3c

## Executive Summary

**CRITICAL FINDING**: The local `apps/` directory is NOT legacy code. It contains an actively running observability system that is running simultaneously with the target system.

## Active Processes Analysis

### Local Apps Directory (Legacy System)
- **Server Process**: PID 2997, 2998 - `bun run dev` in apps/server
- **Client Process**: PID 3021, 3022 - Vite dev server in apps/client
- **Database**: Active SQLite database (events.db, 58MB) with WAL files
- **Port Status**: Likely running on ports 4000 (server) and 5173 (client)

### Target System (New System)
- **Background Processes**: 522e6c, 38988a starting from `/Users/sam/claude-code-hooks-multi-agent-observability/apps/client`
- **Hook Integration**: SessionStart hooks now point to target system
- **Status**: Being started by current SessionStart hooks

## Directory Structure Analysis

### Apps/Server (Multi-Agent Observability Server v2.0.0)
- **Technology**: Bun + TypeScript + SQLite
- **Main Files**: 
  - src/index.ts (24KB) - Main server entry point
  - src/workflow-bridge.ts (19KB) - Workflow integration
  - src/shrimp-mcp-api.ts (9KB) - Task manager API
  - events.db (58MB) - Active event database
- **Configuration**: CLAUDE.md specifying Bun-first development

### Apps/Client (Multi-Agent Observability Client v1.0.0)
- **Technology**: Vue 3 + Vite + TypeScript + D3.js + Tailwind
- **Status**: Full node_modules installation (active development environment)
- **Purpose**: Frontend dashboard for observability data

## Hook System References

Found multiple references in hook scripts to local apps/ directory:
1. `enhanced_monitoring_system.py`: Recommendation to start "bun run dev in apps/server"
2. Multiple log files containing paths to `/Users/sam/claude-code-hooks-mastery/apps/server/src/index.ts`
3. Event tracking data referencing local apps structure

## Comparison with Target System

| Aspect | Local Apps/ | Target System |
|--------|-------------|---------------|
| Location | `/Users/sam/claude-code-hooks-mastery/apps` | `/Users/sam/claude-code-hooks-multi-agent-observability` |
| Status | Currently Running | Being Started by Hooks |
| Integration | Referenced by old hook scripts | Configured in SessionStart hooks |
| Database | 58MB events.db with active data | Unknown/New installation |

## Risk Assessment

### 🔴 HIGH RISK - DO NOT REMOVE

**Reasons:**
1. **Active Production Data**: The local system contains 58MB of observability events in active database
2. **Live Processes**: Multiple active processes depend on this directory structure
3. **Historical Data**: Extensive logging and session data that may be needed for analysis
4. **Parallel Operation**: Both systems appear designed to run simultaneously during transition

### Potential Data Loss Scenarios
- **Event History**: 58MB of collected observability data would be lost
- **Session Logs**: Multiple session directories with valuable debugging information
- **Configuration State**: Local .claude directories with session context

## Recommendations

### ✅ SAFE ACTIONS
1. **Preserve Directory**: Keep apps/ directory intact
2. **Monitor Both Systems**: Allow parallel operation during transition period
3. **Data Migration**: Consider migrating valuable data from old to new system
4. **Gradual Transition**: Phase out old system after confirming new system stability

### ⚠️ CONDITIONAL ACTIONS
1. **Process Management**: Eventually stop old processes after confirming new system works
2. **Database Migration**: Export/import valuable observability data
3. **Archive Strategy**: Move apps/ to archive location rather than delete

### 🔴 NEVER DO
- **Never remove apps/ directory** - contains active production data
- **Never kill processes** without understanding impact on data integrity
- **Never assume legacy** without thorough data migration plan

## Conclusion

The apps/ directory contains a fully functional, actively running observability system with significant production data. It is NOT garbage code but rather a parallel system that should be carefully transitioned rather than removed.

**RECOMMENDATION**: Mark apps/ directory as **CRITICAL - PRESERVE** and focus cleanup efforts on truly obsolete files.