import { Database } from 'bun:sqlite';
import type { HookEvent, FilterOptions, Theme, ThemeSearchQuery, AgentMetadata, AgentStats } from './types';

let db: Database;

export function initDatabase(): void {
  db = new Database('events.db');
  
  // Enable WAL mode for better concurrent performance
  db.exec('PRAGMA journal_mode = WAL');
  db.exec('PRAGMA synchronous = NORMAL');
  
  // Create events table with multi-agent support
  db.exec(`
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_app TEXT NOT NULL,
      session_id TEXT NOT NULL,
      hook_event_type TEXT NOT NULL,
      payload TEXT NOT NULL,
      chat TEXT,
      summary TEXT,
      timestamp INTEGER NOT NULL,
      agent_name TEXT,
      agent_role TEXT,
      agent_category TEXT,
      delegation_chain TEXT
    )
  `);
  
  // Check and add missing columns for migration
  try {
    const columns = db.prepare("PRAGMA table_info(events)").all() as any[];
    const columnNames = columns.map((col: any) => col.name);
    
    // Migrate chat column
    if (!columnNames.includes('chat')) {
      db.exec('ALTER TABLE events ADD COLUMN chat TEXT');
    }
    
    // Migrate summary column
    if (!columnNames.includes('summary')) {
      db.exec('ALTER TABLE events ADD COLUMN summary TEXT');
    }
    
    // Migrate multi-agent columns
    if (!columnNames.includes('agent_name')) {
      db.exec('ALTER TABLE events ADD COLUMN agent_name TEXT');
    }
    if (!columnNames.includes('agent_role')) {
      db.exec('ALTER TABLE events ADD COLUMN agent_role TEXT');
    }
    if (!columnNames.includes('agent_category')) {
      db.exec('ALTER TABLE events ADD COLUMN agent_category TEXT');
    }
    if (!columnNames.includes('delegation_chain')) {
      db.exec('ALTER TABLE events ADD COLUMN delegation_chain TEXT');
    }
  } catch (error) {
    // If the table doesn't exist yet, the CREATE TABLE above will handle it
  }
  
  // Create indexes for common queries
  db.exec('CREATE INDEX IF NOT EXISTS idx_source_app ON events(source_app)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_session_id ON events(session_id)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_hook_event_type ON events(hook_event_type)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)');
  
  // Create indexes for multi-agent queries
  db.exec('CREATE INDEX IF NOT EXISTS idx_agent_name ON events(agent_name)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_agent_role ON events(agent_role)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_agent_category ON events(agent_category)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_delegation_chain ON events(delegation_chain)');
  
  // Create themes table
  db.exec(`
    CREATE TABLE IF NOT EXISTS themes (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL UNIQUE,
      displayName TEXT NOT NULL,
      description TEXT,
      colors TEXT NOT NULL,
      isPublic INTEGER NOT NULL DEFAULT 0,
      authorId TEXT,
      authorName TEXT,
      createdAt INTEGER NOT NULL,
      updatedAt INTEGER NOT NULL,
      tags TEXT,
      downloadCount INTEGER DEFAULT 0,
      rating REAL DEFAULT 0,
      ratingCount INTEGER DEFAULT 0
    )
  `);
  
  // Create theme shares table
  db.exec(`
    CREATE TABLE IF NOT EXISTS theme_shares (
      id TEXT PRIMARY KEY,
      themeId TEXT NOT NULL,
      shareToken TEXT NOT NULL UNIQUE,
      expiresAt INTEGER,
      isPublic INTEGER NOT NULL DEFAULT 0,
      allowedUsers TEXT,
      createdAt INTEGER NOT NULL,
      accessCount INTEGER DEFAULT 0,
      FOREIGN KEY (themeId) REFERENCES themes (id) ON DELETE CASCADE
    )
  `);
  
  // Create theme ratings table
  db.exec(`
    CREATE TABLE IF NOT EXISTS theme_ratings (
      id TEXT PRIMARY KEY,
      themeId TEXT NOT NULL,
      userId TEXT NOT NULL,
      rating INTEGER NOT NULL,
      comment TEXT,
      createdAt INTEGER NOT NULL,
      UNIQUE(themeId, userId),
      FOREIGN KEY (themeId) REFERENCES themes (id) ON DELETE CASCADE
    )
  `);
  
  // Create indexes for theme tables
  db.exec('CREATE INDEX IF NOT EXISTS idx_themes_name ON themes(name)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_themes_isPublic ON themes(isPublic)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_themes_createdAt ON themes(createdAt)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_theme_shares_token ON theme_shares(shareToken)');
  db.exec('CREATE INDEX IF NOT EXISTS idx_theme_ratings_theme ON theme_ratings(themeId)');
}

export function insertEvent(event: HookEvent): HookEvent {
  const stmt = db.prepare(`
    INSERT INTO events (source_app, session_id, hook_event_type, payload, chat, summary, timestamp, agent_name, agent_role, agent_category, delegation_chain)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  
  const timestamp = event.timestamp || Date.now();
  const result = stmt.run(
    event.source_app,
    event.session_id,
    event.hook_event_type,
    JSON.stringify(event.payload),
    event.chat ? JSON.stringify(event.chat) : null,
    event.summary || null,
    timestamp,
    event.agent_name || null,
    event.agent_role || null,
    event.agent_category || null,
    event.delegation_chain || null
  );
  
  return {
    ...event,
    id: result.lastInsertRowid as number,
    timestamp
  };
}

export function getFilterOptions(): FilterOptions {
  const sourceApps = db.prepare('SELECT DISTINCT source_app FROM events ORDER BY source_app').all() as { source_app: string }[];
  const sessionIds = db.prepare('SELECT DISTINCT session_id FROM events ORDER BY session_id DESC LIMIT 100').all() as { session_id: string }[];
  const hookEventTypes = db.prepare('SELECT DISTINCT hook_event_type FROM events ORDER BY hook_event_type').all() as { hook_event_type: string }[];
  
  // Get agent filter options
  const agentNames = db.prepare('SELECT DISTINCT agent_name FROM events WHERE agent_name IS NOT NULL ORDER BY agent_name').all() as { agent_name: string }[];
  const agentRoles = db.prepare('SELECT DISTINCT agent_role FROM events WHERE agent_role IS NOT NULL ORDER BY agent_role').all() as { agent_role: string }[];
  const agentCategories = db.prepare('SELECT DISTINCT agent_category FROM events WHERE agent_category IS NOT NULL ORDER BY agent_category').all() as { agent_category: string }[];
  
  return {
    source_apps: sourceApps.map(row => row.source_app),
    session_ids: sessionIds.map(row => row.session_id),
    hook_event_types: hookEventTypes.map(row => row.hook_event_type),
    agent_names: agentNames.map(row => row.agent_name),
    agent_roles: agentRoles.map(row => row.agent_role),
    agent_categories: agentCategories.map(row => row.agent_category)
  };
}

export function getRecentEvents(limit: number = 100): HookEvent[] {
  const stmt = db.prepare(`
    SELECT id, source_app, session_id, hook_event_type, payload, chat, summary, timestamp, 
           agent_name, agent_role, agent_category, delegation_chain
    FROM events
    ORDER BY timestamp DESC
    LIMIT ?
  `);
  
  const rows = stmt.all(limit) as any[];
  
  return rows.map(row => ({
    id: row.id,
    source_app: row.source_app,
    session_id: row.session_id,
    hook_event_type: row.hook_event_type,
    payload: JSON.parse(row.payload),
    chat: row.chat ? JSON.parse(row.chat) : undefined,
    summary: row.summary || undefined,
    timestamp: row.timestamp,
    agent_name: row.agent_name || undefined,
    agent_role: row.agent_role || undefined,
    agent_category: row.agent_category || undefined,
    delegation_chain: row.delegation_chain || undefined
  })).reverse();
}

// Theme database functions
export function insertTheme(theme: Theme): Theme {
  const stmt = db.prepare(`
    INSERT INTO themes (id, name, displayName, description, colors, isPublic, authorId, authorName, createdAt, updatedAt, tags, downloadCount, rating, ratingCount)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  
  stmt.run(
    theme.id,
    theme.name,
    theme.displayName,
    theme.description || null,
    JSON.stringify(theme.colors),
    theme.isPublic ? 1 : 0,
    theme.authorId || null,
    theme.authorName || null,
    theme.createdAt,
    theme.updatedAt,
    JSON.stringify(theme.tags),
    theme.downloadCount || 0,
    theme.rating || 0,
    theme.ratingCount || 0
  );
  
  return theme;
}

export function updateTheme(id: string, updates: Partial<Theme>): boolean {
  const allowedFields = ['displayName', 'description', 'colors', 'isPublic', 'updatedAt', 'tags'];
  const setClause = Object.keys(updates)
    .filter(key => allowedFields.includes(key))
    .map(key => `${key} = ?`)
    .join(', ');
  
  if (!setClause) return false;
  
  const values = Object.keys(updates)
    .filter(key => allowedFields.includes(key))
    .map(key => {
      if (key === 'colors' || key === 'tags') {
        return JSON.stringify(updates[key as keyof Theme]);
      }
      if (key === 'isPublic') {
        return updates[key as keyof Theme] ? 1 : 0;
      }
      return updates[key as keyof Theme];
    });
  
  const stmt = db.prepare(`UPDATE themes SET ${setClause} WHERE id = ?`);
  const result = stmt.run(...values, id);
  
  return result.changes > 0;
}

export function getTheme(id: string): Theme | null {
  const stmt = db.prepare('SELECT * FROM themes WHERE id = ?');
  const row = stmt.get(id) as any;
  
  if (!row) return null;
  
  return {
    id: row.id,
    name: row.name,
    displayName: row.displayName,
    description: row.description,
    colors: JSON.parse(row.colors),
    isPublic: Boolean(row.isPublic),
    authorId: row.authorId,
    authorName: row.authorName,
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
    tags: JSON.parse(row.tags || '[]'),
    downloadCount: row.downloadCount,
    rating: row.rating,
    ratingCount: row.ratingCount
  };
}

export function getThemes(query: ThemeSearchQuery = {}): Theme[] {
  let sql = 'SELECT * FROM themes WHERE 1=1';
  const params: any[] = [];
  
  if (query.isPublic !== undefined) {
    sql += ' AND isPublic = ?';
    params.push(query.isPublic ? 1 : 0);
  }
  
  if (query.authorId) {
    sql += ' AND authorId = ?';
    params.push(query.authorId);
  }
  
  if (query.query) {
    sql += ' AND (name LIKE ? OR displayName LIKE ? OR description LIKE ?)';
    const searchTerm = `%${query.query}%`;
    params.push(searchTerm, searchTerm, searchTerm);
  }
  
  // Add sorting
  const sortBy = query.sortBy || 'created';
  const sortOrder = query.sortOrder || 'desc';
  const sortColumn = {
    name: 'name',
    created: 'createdAt',
    updated: 'updatedAt',
    downloads: 'downloadCount',
    rating: 'rating'
  }[sortBy] || 'createdAt';
  
  sql += ` ORDER BY ${sortColumn} ${sortOrder.toUpperCase()}`;
  
  // Add pagination
  if (query.limit) {
    sql += ' LIMIT ?';
    params.push(query.limit);
    
    if (query.offset) {
      sql += ' OFFSET ?';
      params.push(query.offset);
    }
  }
  
  const stmt = db.prepare(sql);
  const rows = stmt.all(...params) as any[];
  
  return rows.map(row => ({
    id: row.id,
    name: row.name,
    displayName: row.displayName,
    description: row.description,
    colors: JSON.parse(row.colors),
    isPublic: Boolean(row.isPublic),
    authorId: row.authorId,
    authorName: row.authorName,
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
    tags: JSON.parse(row.tags || '[]'),
    downloadCount: row.downloadCount,
    rating: row.rating,
    ratingCount: row.ratingCount
  }));
}

export function deleteTheme(id: string): boolean {
  const stmt = db.prepare('DELETE FROM themes WHERE id = ?');
  const result = stmt.run(id);
  return result.changes > 0;
}

export function incrementThemeDownloadCount(id: string): boolean {
  const stmt = db.prepare('UPDATE themes SET downloadCount = downloadCount + 1 WHERE id = ?');
  const result = stmt.run(id);
  return result.changes > 0;
}

// Multi-Agent Statistics Functions
export function getAgentStats(): AgentStats {
  const totalAgentsStmt = db.prepare('SELECT COUNT(DISTINCT agent_name) as count FROM events WHERE agent_name IS NOT NULL');
  const totalAgents = (totalAgentsStmt.get() as any)?.count || 0;
  
  // Active agents in last 24 hours
  const activeAgentsStmt = db.prepare(`
    SELECT COUNT(DISTINCT agent_name) as count 
    FROM events 
    WHERE agent_name IS NOT NULL 
    AND timestamp > ?
  `);
  const activeAgents = (activeAgentsStmt.get(Date.now() - 24 * 60 * 60 * 1000) as any)?.count || 0;
  
  // Agents by category
  const categoriesStmt = db.prepare(`
    SELECT agent_category, COUNT(DISTINCT agent_name) as count 
    FROM events 
    WHERE agent_category IS NOT NULL 
    GROUP BY agent_category
  `);
  const categoryRows = categoriesStmt.all() as any[];
  const agentsByCategory: Record<string, number> = {};
  categoryRows.forEach(row => {
    agentsByCategory[row.agent_category] = row.count;
  });
  
  // Agents by role
  const rolesStmt = db.prepare(`
    SELECT agent_role, COUNT(DISTINCT agent_name) as count 
    FROM events 
    WHERE agent_role IS NOT NULL 
    GROUP BY agent_role
  `);
  const roleRows = rolesStmt.all() as any[];
  const agentsByRole: Record<string, number> = {};
  roleRows.forEach(row => {
    agentsByRole[row.agent_role] = row.count;
  });
  
  // Delegation patterns
  const delegationStmt = db.prepare(`
    SELECT delegation_chain, COUNT(*) as count 
    FROM events 
    WHERE delegation_chain IS NOT NULL 
    GROUP BY delegation_chain
  `);
  const delegationRows = delegationStmt.all() as any[];
  const delegationPatterns: Record<string, number> = {};
  delegationRows.forEach(row => {
    delegationPatterns[row.delegation_chain] = row.count;
  });
  
  return {
    total_agents: totalAgents,
    active_agents: activeAgents,
    agents_by_category: agentsByCategory,
    agents_by_role: agentsByRole,
    delegation_patterns: delegationPatterns
  };
}

export function getAgentMetadata(): AgentMetadata[] {
  const stmt = db.prepare(`
    SELECT 
      agent_name,
      agent_role,
      agent_category,
      delegation_chain,
      COUNT(*) as event_count,
      MAX(timestamp) as last_activity,
      AVG(CASE WHEN hook_event_type = 'SubagentStop' THEN 1 ELSE 0 END) as success_rate
    FROM events
    WHERE agent_name IS NOT NULL
    GROUP BY agent_name, agent_role, agent_category, delegation_chain
    ORDER BY last_activity DESC
  `);
  
  const rows = stmt.all() as any[];
  
  return rows.map(row => ({
    agent_name: row.agent_name,
    agent_role: row.agent_role,
    agent_category: row.agent_category,
    delegation_chain: row.delegation_chain,
    event_count: row.event_count,
    last_activity: row.last_activity,
    success_rate: row.success_rate || 0
  }));
}

export function getAgentActivity(agentName: string, limit: number = 50): HookEvent[] {
  const stmt = db.prepare(`
    SELECT id, source_app, session_id, hook_event_type, payload, chat, summary, timestamp,
           agent_name, agent_role, agent_category, delegation_chain
    FROM events
    WHERE agent_name = ?
    ORDER BY timestamp DESC
    LIMIT ?
  `);
  
  const rows = stmt.all(agentName, limit) as any[];
  
  return rows.map(row => ({
    id: row.id,
    source_app: row.source_app,
    session_id: row.session_id,
    hook_event_type: row.hook_event_type,
    payload: JSON.parse(row.payload),
    chat: row.chat ? JSON.parse(row.chat) : undefined,
    summary: row.summary || undefined,
    timestamp: row.timestamp,
    agent_name: row.agent_name,
    agent_role: row.agent_role,
    agent_category: row.agent_category,
    delegation_chain: row.delegation_chain
  }));
}