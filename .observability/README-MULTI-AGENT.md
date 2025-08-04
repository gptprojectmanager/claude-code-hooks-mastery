# Multi-Agent Observability System

A comprehensive real-time monitoring dashboard for Claude Code's 14 sub-agents, providing visibility into agent activities, performance metrics, and coordination patterns.

## Features

### 🤖 Multi-Agent Support
- **14 Sub-Agents Monitoring**: Track all Claude Code sub-agents in real-time
- **Agent Categorization**: Organize by role (Core Development, Quality, Security, etc.)
- **Delegation Tracking**: Monitor Primary → Specialist delegation patterns
- **Individual Agent Performance**: Success rates, completion times, activity levels

### 📊 Real-Time Dashboard
- **Live Event Stream**: WebSocket-powered real-time updates
- **Agent Grid View**: Visual status indicators for all agents
- **Activity Charts**: Hourly event distribution and trends
- **Delegation Flow Visualization**: See how agents coordinate

### 🔒 Security Monitoring
- **Dangerous Command Detection**: Blocks `rm -rf` and similar commands
- **Environment File Protection**: Prevents access to `.env` files
- **Agent-Specific Security Events**: Track security violations per agent
- **Audit Trail**: Complete history of security-related events

### 📈 Performance Analytics
- **Agent Statistics**: Event counts, success rates, last activity
- **Category Analytics**: Performance by agent category
- **Delegation Patterns**: Most common coordination workflows
- **Time-Series Data**: Historical performance trends

## Quick Start

### Prerequisites
- [Bun](https://bun.sh/) runtime installed
- Claude Code with hooks configured

### Installation

1. **Start the Observability Server**
   ```bash
   cd .observability/server
   ./start.sh
   ```

2. **Access the Dashboard**
   - Open http://localhost:4000 in your browser
   - View real-time agent activity and coordination

3. **Enable Hook Integration**
   The hooks are automatically configured to send events when:
   - `OBSERVABILITY_ENABLED=true` (default)
   - Server is running on `http://localhost:4000`

## Agent Categories

### Core Development Team (8 agents)
- **primary-agent** - Team orchestrator and coordinator
- **planner** - Task planning and decomposition  
- **coder** - Code implementation and development
- **code-reviewer** - Code review and quality assurance
- **tester-debugger** - Testing, debugging, and validation
- **optimizer** - Performance optimization and tuning
- **system-admin** - DevOps, infrastructure, and automation
- **researcher** - Research, documentation, and analysis

### Quality Assurance (4 agents)
- **code-reviewer** - Code quality and standards
- **tester-debugger** - Testing and debugging
- **cleanup-validator** - Code cleanup and validation
- **github-copilot-reviewer** - Automated code review

### Security (2 agents)
- **security-specialist** - Security analysis and hardening
- **code-reviewer** - Security-focused code review

### Design & Architecture (3 agents)
- **database-architect** - Database design and optimization
- **ui-ux-designer** - User interface and experience design
- **optimizer** - Performance and architectural optimization

### Domain Specialists (5 agents)
- **mathematician** - Mathematical computations and algorithms
- **researcher** - Academic research and documentation
- **security-specialist** - Security expertise
- **database-architect** - Data architecture
- **ui-ux-designer** - Design expertise

## API Endpoints

### Events
- `POST /api/events` - Submit new events with agent metadata
- `GET /events/recent` - Retrieve recent events (legacy)
- `GET /events/filter-options` - Get available filter options

### Agent Analytics
- `GET /api/agents/stats` - Overall agent statistics
- `GET /api/agents/metadata` - All agent metadata and performance
- `GET /api/agents/{name}/activity` - Specific agent activity history

### System Health
- `GET /api/health` - Health check with multi-agent capabilities

### WebSocket
- `ws://localhost:4000/stream` - Real-time event stream

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
# Server Configuration
OBSERVABILITY_SERVER_URL=http://localhost:4000
OBSERVABILITY_PORT=4000
OBSERVABILITY_ENABLED=true

# Security Configuration
SECURITY_MONITORING_ENABLED=true
DANGEROUS_COMMAND_DETECTION=true
ENV_FILE_PROTECTION=true

# Dashboard Configuration
DASHBOARD_ENABLED=true
DASHBOARD_AUTO_REFRESH=true
```

## Hook Integration

The system automatically enhances Claude Code hooks with agent metadata:

### SubagentStop Hook
```bash
uv run .claude/hooks/subagent_stop.py --send-observability
```

### PreToolUse Hook
- Detects current agent from environment
- Monitors security violations per agent
- Tracks tool usage patterns

### Agent Detection
The system uses multiple methods to identify the current agent:
1. Environment variables (`CLAUDE_AGENT_NAME`)
2. Process analysis and command line parsing
3. Log file analysis for recent agent activity
4. Fallback to `primary-agent`

## Database Schema

### Events Table
```sql
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_app TEXT NOT NULL,
  session_id TEXT NOT NULL,
  hook_event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  chat TEXT,
  summary TEXT,
  timestamp INTEGER NOT NULL,
  -- Multi-Agent Fields
  agent_name TEXT,
  agent_role TEXT,
  agent_category TEXT,
  delegation_chain TEXT
);
```

### Indexes
- `idx_agent_name` - Fast agent filtering
- `idx_agent_role` - Role-based queries
- `idx_agent_category` - Category analytics
- `idx_delegation_chain` - Delegation pattern analysis

## Security Features

### Command Protection
- **Dangerous Commands**: Blocks `rm -rf`, `rm --recursive --force`
- **Path Protection**: Prevents deletion of system directories
- **Environment Protection**: Blocks access to `.env` files

### Agent-Specific Security
- Track security violations per agent
- Audit trail for all blocked commands
- Risk assessment by agent category

### Privacy Protection
- Tool input truncation in logs
- Session ID anonymization in display
- Configurable data retention

## Performance Optimization

### Database
- SQLite with WAL mode for concurrent access
- Strategic indexing for multi-agent queries
- Automatic migration for schema updates

### Real-Time Updates
- WebSocket with automatic reconnection
- Efficient event filtering and pagination
- Client-side caching and state management

### Resource Management
- Event retention policies (90 days default)
- Log rotation and cleanup
- Connection pooling and cleanup

## Development

### Adding New Agent Categories
1. Update `AGENT_CATEGORIES` in `utils/agent_detector.py`
2. Add role mapping in `AGENT_ROLES`
3. Update dashboard filters and styling

### Custom Event Types
1. Add event type to hooks with appropriate metadata
2. Update dashboard event type filter
3. Add specific visualizations if needed

### Extending Analytics
1. Add new database queries in `src/db.ts`
2. Create API endpoints in `src/index.ts`
3. Update dashboard with new visualizations

## Troubleshooting

### Connection Issues
- Verify server is running on correct port
- Check firewall settings for port 4000
- Ensure WebSocket connections are allowed

### Missing Agent Data
- Verify hooks are properly configured
- Check `OBSERVABILITY_ENABLED` setting
- Review agent detection in `utils/agent_detector.py`

### Performance Issues
- Monitor database size and optimize queries
- Adjust event retention settings
- Check WebSocket client count

## Contributing

1. Follow existing code patterns
2. Update tests for new features
3. Document API changes
4. Test with multiple agents simultaneously

## License

MIT License - See LICENSE file for details

---

**Built for Claude Code Multi-Agent Coordination**  
Real-time observability for modern AI development workflows.