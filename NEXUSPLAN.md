# NEXUSPLAN 3.0: A Unified Implementation Strategy

This document outlines the comprehensive implementation strategy for NEXUSPLAN 3.0, integrating the strengths of six key systems into a single, cohesive platform.

## 1. MAXIMUM CODE REUSE STRATEGY

The primary goal is to leverage the mature components of each system to accelerate development and ensure stability.

### Components for Reuse:

1.  **Vibe-Kanban:**
    *   **Component:** Real-time Svelte frontend dashboard.
    *   **Files:** `vibe-kanban/src/client/` (entire directory).
    *   **Action:** Copy to `apps/client/`. This will become the primary user interface for monitoring and interaction.

2.  **OpenEvolve:**
    *   **Component:** Core genetic algorithm and optimization engine.
    *   **Files:** `openevolve/src/engine/` and `openevolve/src/models.py`.
    *   **Action:** Copy to `apps/server/src/evolution_engine/`. These modules will run as a background service, operating on data in the unified database.

3.  **Cipher & RAG-Anything:**
    *   **Component:** Data ingestion pipelines, Qdrant client logic, and document processing utilities.
    *   **Files:** `rag-anything/src/ingestion/`, `rag-anything/src/retrieval/`, `cipher/src/graph_builder/`.
    *   **Action:** Consolidate these into a new `apps/server/src/data_pipelines/` directory. This creates a unified service for all knowledge-base-related operations.

4.  **BMad Agent Framework:**
    *   **Component:** Core agent logic, task management, and tool-use orchestration.
    *   **Files:** `bmad/src/agent/` and `bmad/src/tools/`.
    *   **Action:** Copy to `apps/server/src/agent_framework/`. This will serve as the high-level cognitive core for agents.

5.  **Enhanced Tmux Agent:**
    *   **Component:** Sandboxed code execution environment.
    *   **Files:** The Tmux session management scripts.
    *   **Action:** Place scripts in `scripts/agent_executor/`. The BMad agent will call these scripts to execute code in an isolated environment.

### Overall Code Reuse Calculation:

By porting these core, feature-complete modules, we avoid rewriting the most complex parts of the system.
- **Frontend:** 100% reuse (Vibe-Kanban)
- **Data Pipelines:** 90% reuse (RAG-Anything, Cipher)
- **Agent Core:** 85% reuse (BMad)
- **Optimization Engine:** 95% reuse (OpenEvolve)

This results in an estimated **overall code reuse of approximately 75-80%**, leaving only integration logic and API facades to be developed.

## 2. DATABASE ARCHITECTURE

The database architecture will be a hybrid model designed for performance, scalability, and specific data types.

1.  **SQLite Integration:**
    *   A single SQLite database (`data/nexus.db`) will serve as the primary store for structured, relational data.
    *   **Schema:** Tables will be namespaced to avoid collisions.
        *   `openevolve_experiments`, `openevolve_results` (from OpenEvolve)
        *   `kanban_cards`, `kanban_lanes` (from Vibe-Kanban)
        *   `agent_tasks`, `agent_logs` (for the new agent framework)
    *   **Benefit:** This provides a lightweight, zero-configuration database for operational data that requires transactional integrity.

2.  **Qdrant Integration:**
    *   Qdrant will remain the dedicated vector store for the memory layer.
    *   **Collections:** We will unify into two primary collections:
        *   `nexus_documents`: For storing raw text chunks and source document metadata (from RAG-Anything).
        *   `nexus_graph_nodes`: For storing vector representations of entities and concepts (from Cipher).
    *   **Action:** The data pipeline services will be configured to write to these specific collections, with metadata indicating the original source.

3.  **Redis Usage Optimization:**
    *   Redis will be used exclusively as a high-speed, non-persistent message bus and cache.
    *   **Primary Use Cases:**
        1.  **Inter-service Communication:** Publishing events (e.g., `hook:triggered`, `ingestion:complete`, `agent:task_started`).
        2.  **Real-time Dashboard:** The backend will push messages to a Redis Pub/Sub channel, which the Vibe-Kanban frontend will subscribe to via WebSockets.
        3.  **Short-Term Caching:** Caching expensive queries or LLM calls for a few minutes.
    *   **Constraint:** No service should rely on Redis for persistent data storage.

## 3. MONITORING ARCHITECTURE

The monitoring system will provide a unified, real-time view of the entire NEXUS platform.

1.  **Vibe-Kanban Dashboard Leverage:**
    *   The copied Vibe-Kanban frontend will be the central monitoring UI.
    *   **Action:** Its WebSocket client will be pointed to a new backend service that subscribes to all relevant Redis channels. It will be modified to display agent status, system metrics, and hook events alongside the Kanban boards.

2.  **Claude Code Hooks Integration:**
    *   The existing hooks (`.claude/hooks/`) will be modified.
    *   **Action:** Instead of logging to files or stdout, each hook will publish a structured JSON message to a specific Redis channel (e.g., `hooks:pre-prompt`). This immediately makes all hook activity available to the rest of the system.

3.  **MacBook System Metrics Collection:**
    *   A new lightweight Python service will be created.
    *   **Path:** `apps/monitoring_service/collector.py`
    *   **Logic:** The script will use the `psutil` library to collect CPU usage, memory consumption, and disk I/O.
    *   **Action:** Every 5 seconds, it will publish these metrics to the `system:metrics:macbook` Redis channel.

4.  **Grafana Dashboard Unification:**
    *   For long-term metrics and professional dashboards, Grafana is ideal.
    *   **Strategy:**
        1.  Deploy Prometheus via Docker Compose.
        2.  The new `monitoring_service` and other Python backends will expose a `/metrics` endpoint using the `prometheus-client` library.
        3.  Prometheus will scrape these endpoints.
        4.  Grafana will be configured with Prometheus as a data source, allowing for the creation of detailed, persistent dashboards that track system health over time.

## 4. QUICK START IMPLEMENTATION (Days 1-3)

This is an aggressive but achievable plan for initial setup and integration.

### Day 1: Foundation & Scaffolding

1.  **Create Directory Structure:**
    ```bash
    mkdir -p apps/client apps/server/src/{data_pipelines,evolution_engine,agent_framework} apps/monitoring_service data scripts/agent_executor
    ```
2.  **Initialize Docker Compose:** Create a root `docker-compose.yml` with initial service definitions.
    ```yaml
    version: '3.8'
    services:
      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"
      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - "6333:6333"
      nexus_backend:
        build: ./apps/server
        volumes:
          - ./apps/server/src:/app/src
          - ./data:/app/data
        ports:
          - "8000:8000"
        depends_on:
          - redis
          - qdrant
    ```
3.  **Setup Python Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt # Assuming a consolidated requirements file
    ```

### Day 2: Codebase Integration

1.  **Copy Vibe-Kanban Frontend:**
    ```bash
    cp -R /path/to/vibe-kanban/src/client/ apps/client/
    ```
2.  **Copy RAG & Cipher Pipelines:**
    ```bash
    cp -R /path/to/rag-anything/src/ingestion/ apps/server/src/data_pipelines/
    cp -R /path/to/rag-anything/src/retrieval/ apps/server/src/data_pipelines/
    cp -R /path/to/cipher/src/graph_builder/ apps/server/src/data_pipelines/
    ```
3.  **Copy BMad Agent:**
    ```bash
    cp -R /path/to/bmad/src/agent/ apps/server/src/agent_framework/
    ```
4.  **Copy OpenEvolve Engine:**
    ```bash
    cp -R /path/to/openevolve/src/engine/ apps/server/src/evolution_engine/
    ```

### Day 3: Configuration & Initial Testing

1.  **Configure Services:** Update the copied code to use environment variables for database hosts (Redis, Qdrant) and file paths (`/app/data/nexus.db`).
2.  **Build and Run Containers:**
    ```bash
    docker-compose up --build -d
    ```
3.  **Initial Integration Test:**
    *   **Goal:** Verify the hook-to-dashboard pipeline.
    *   **Steps:**
        1.  Manually trigger a Claude Code hook (e.g., by running a command in the CLI).
        2.  Connect to the Redis container (`redis-cli`) and `SUBSCRIBE` to the `hooks:pre-prompt` channel to confirm the message is being published.
        3.  Open the Vibe-Kanban dashboard in a browser.
        4.  Confirm that the event appears in the real-time event log on the dashboard.

## 5. ARCHITECTURAL DECISIONS

These decisions define the core architecture of the NEXUS platform.

1.  **Backbone System:**
    *   The **Claude Code Hooks Mastery** project itself will serve as the central backbone. Its event-driven nature, triggered by user and AI actions, is the perfect orchestrator for the entire system. All other systems are integrated as services that react to these core events.

2.  **Combined Agent Framework:**
    *   A two-layer model will be used:
        *   **Cognitive Layer (BMad):** Responsible for high-level reasoning, planning, and tool selection.
        *   **Execution Layer (Enhanced Tmux):** The BMad agent will delegate all code execution and shell commands to the Tmux executor, which provides a secure, sandboxed environment. This separates thought from action.

3.  **Memory Layer Architecture:**
    *   A hybrid memory system will be implemented:
        *   **Long-Term Memory (LTM):** Stored in Qdrant. This is where semantic knowledge, documents, and conceptual graphs reside. Accessed via the unified data pipelines.
        *   **Working Memory (WM):** Stored in the SQLite database. This includes the agent's current task list, scratchpad, recent conversation history, and the state of the Kanban board. It is structured and accessed via SQL queries.

4.  **Evolution/Optimization Engine Placement:**
    *   The OpenEvolve engine will run as an **asynchronous, background service**. It will not be in the real-time agent loop.
    *   **Workflow:** It will periodically query the SQLite database for agent performance logs and task outcomes. Based on this data, it will generate and test new prompts, tool sequences, or agent configurations, writing the results of these experiments back to the `openevolve_results` table for review and potential promotion into the main agent's configuration.
