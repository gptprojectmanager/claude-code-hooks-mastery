### Summary of Claude Code Sub-Agents

This document provides a summary of how to effectively use Claude Code sub-agents, based on the provided video transcript.

#### Core Concepts

*   **What are Sub-Agents?**
    *   Sub-agents are specialized, autonomous agents that perform specific tasks.
    *   They are triggered and prompted by a primary agent, not directly by the user.
*   **Information Flow:**
    1.  The user prompts the primary Claude Code agent.
    2.  The primary agent, based on the user's prompt, prompts one or more sub-agents.
    3.  Sub-agents execute their tasks autonomously.
    4.  Sub-agents report their results back to the primary agent.
    5.  The primary agent reports the final result to the user.
*   **System Prompts vs. User Prompts:**
    *   The prompt you write for a sub-agent is its **system prompt**, which defines its core purpose and behavior. It is not a one-time user prompt.
    *   This is a critical distinction that affects how you design and write sub-agent prompts.

#### Common Mistakes to Avoid

1.  **Misunderstanding the Information Flow:** Many engineers mistakenly believe they are directly prompting the sub-agent. You are always communicating with the primary agent, which then delegates tasks.
2.  **Incorrect Prompting:** Not realizing you are writing a **system prompt** for the sub-agent leads to ineffective or incorrect agent behavior. You must explicitly instruct the sub-agent on how to report its findings back to the primary agent.

#### Best Practices for Building Sub-Agents

*   **Explicit Reporting:** In the sub-agent's system prompt, include a "Report" or "Response Format" section that clearly defines how it should communicate its results back to the primary agent.
*   **Leverage the Description:** The `description` field in a sub-agent's configuration is crucial. The primary agent uses this to determine *when* and *how* to call the sub-agent.
    *   Use concrete triggers (e.g., "If the user says 'TTS', use this agent").
    *   Provide instructions to the primary agent on how to prompt the sub-agent effectively.
*   **Problem-Solution-Technology Workflow:**
    1.  **Problem:** Start with a clear problem you want to solve.
    2.  **Solution:** Define a clear solution.
    3.  **Technology:** Only then, use the technology (like sub-agents) to implement the solution.
*   **Isolated Context:** Remember that each sub-agent operates in its own isolated context window. It has no memory of the main conversation. The primary agent must provide all necessary information in its prompt to the sub-agent.

#### Benefits of Sub-Agents

*   **Context Preservation:** The main conversation with the primary agent remains clean, as each sub-agent operates in an isolated context.
*   **Specialized Expertise:** You can create highly focused agents with specific tools and instructions.
*   **Reusability:** Build a library of agents for common tasks within your codebase.
*   **Flexible Permissions:** Lock down which tools each sub-agent can access.
*   **Simple Multi-Agent Orchestration:** Combine sub-agents with custom commands (`/`) and hooks to create powerful, chained workflows.

#### Challenges and Issues

*   **Lack of Context History:** The isolation of sub-agents is also a drawback. They only know what the primary agent tells them in a given prompt.
*   **Debugging:** It can be difficult to debug sub-agent workflows, as the full details of the prompts and tool calls are not always visible.
*   **Decision Overload:** As the number of agents grows, the primary agent might become confused about which one to call. Clear and specific descriptions are essential to mitigate this.
*   **Dependency Coupling:** Chaining agents together can create complex dependencies. A change in one agent can break the entire chain. It's best to keep workflows as isolated as possible.
*   **No Nested Sub-Agents:** You cannot call a sub-agent from within another sub-agent.