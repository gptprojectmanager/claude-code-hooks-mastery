---
allowed-tools: Task, TodoWrite, Read, Write, Bash
argument-hint: project_goals_or_requirements
description: Execute comprehensive project planning using primary agent orchestration and Shrimp task management
---

# Planner Command

Esegui planning completo di progetto utilizzando primary agent orchestration, Shrimp task manager, e systematic decomposition.

## Variables

- **GOALS**: $ARGUMENTS or "software development project" if not specified
  - Project goals o requirements (es. "e-commerce platform development", "AI system implementation")
  - Used by: primary-agent-opusplan e supporting planning agents

## Planning Agent Ensemble

### Primary Planning Orchestrator
- @agent-primary-agent-opusplan (complex project orchestration e strategic planning)

### Supporting Planning Specialists
- @agent-primary-agent-opus (standard multi-agent coordination)
- @agent-backend-architect-sonnet (technical architecture planning)
- @agent-ai-engineer-opus (AI/ML project planning)
- @agent-work-validator-opus (plan validation e feasibility assessment)

## Comprehensive Planning Process

### Phase 1: Project Analysis (20 mins)
```
1. Goals e objectives clarification
2. Stakeholder identification e requirements
3. Constraint analysis (timeline, budget, resources)
4. Success criteria definition
5. Risk preliminary assessment
```

### Phase 2: Strategic Decomposition (30 mins)
```
1. Major workstream identification
2. Feature breakdown e prioritization
3. Dependency mapping e critical path
4. Resource requirement estimation
5. Technology stack recommendations
```

### Phase 3: Task Management Setup (25 mins)
```
1. Shrimp task manager initialization
2. Hierarchical task breakdown structure
3. Task dependencies e sequencing
4. Sprint/milestone planning
5. Agent assignment planning
```

### Phase 4: Execution Strategy (15 mins)
```
1. Multi-agent orchestration strategy
2. Workflow automation planning
3. Quality gate definition
4. Progress tracking methodology
5. Risk mitigation planning
```

## Project Planning Methodologies

### Agile Planning Approach
```
- Epic breakdown into user stories
- Sprint planning con velocity estimation
- Backlog prioritization e refinement
- Retrospective planning e improvement cycles
```

### Waterfall Planning Approach
```
- Sequential phase planning
- Detailed upfront requirements analysis
- Comprehensive documentation planning
- Quality gate e approval processes
```

### Hybrid Planning Approach
```
- Agile development con waterfall governance
- Architecture-first iterative planning
- Risk-driven milestone planning
- Flexible scope con fixed timeline
```

## Shrimp Task Manager Integration

### Task Hierarchy Structure
```
PROJECT_LEVEL
├── EPIC_1 (Major Feature/Workstream)
│   ├── STORY_1.1 (User Story/Component)
│   │   ├── TASK_1.1.1 (Development Task)
│   │   ├── TASK_1.1.2 (Testing Task)
│   │   └── TASK_1.1.3 (Documentation Task)
│   └── STORY_1.2
├── EPIC_2
└── EPIC_N
```

### Task Attributes
- **Priority**: Critical, High, Medium, Low
- **Complexity**: Simple, Medium, Complex
- **Dependencies**: Prerequisite tasks e blockers
- **Agent Assignment**: Specialized agent recommendations
- **Estimation**: Time e effort estimates
- **Verification Criteria**: Acceptance criteria e quality gates

## Planning Deliverables

```
project_plan/
└── plan_<timestamp>/
    ├── project_charter/     # Goals, scope, stakeholders
    ├── requirements/        # Functional e non-functional requirements
    ├── architecture/        # High-level system architecture
    ├── task_breakdown/      # Detailed WBS e Shrimp tasks
    ├── timeline/           # Gantt charts e milestone planning
    ├── resource_plan/      # Team structure e agent assignments
    ├── risk_management/    # Risk register e mitigation plans
    └── governance/         # Quality gates e approval processes
```

## Project Planning Templates

### Software Development Project
```
1. Requirements Analysis (Architect + Analyst)
2. System Design (Backend + Frontend + Database)
3. Development Phases (Language Specialists)
4. Testing Strategy (Tester + Security)
5. Deployment Planning (DevOps + Cloud)
```

### AI/ML Project Planning
```
1. Data Strategy (Data Engineer + AI Engineer)
2. Model Development (AI Engineer + Mathematician)
3. Pipeline Architecture (Data + Backend)
4. Integration Planning (Backend + Frontend)
5. MLOps Setup (DevOps + AI Engineer)
```

### Enterprise Integration Project
```
1. System Analysis (Backend + Security)
2. Integration Design (Architect + API Developer)
3. Migration Planning (DevOps + Database)
4. Security Implementation (Security + Auditor)
5. Change Management (Business Analyst)
```

## Quality Gates & Validation

### Planning Quality Criteria
- **Completeness**: All major areas covered
- **Feasibility**: Realistic timelines e resource estimates
- **Risk Management**: Comprehensive risk identification
- **Stakeholder Alignment**: Clear communication e expectations
- **Measurability**: Objective success criteria

### Plan Validation Process
```
1. Technical feasibility review (Architects)
2. Resource availability verification (Project Managers)
3. Risk assessment validation (Risk Specialists)
4. Timeline realism check (Delivery Managers)
5. Stakeholder sign-off (Business Stakeholders)
```

## Execution Monitoring

### Progress Tracking
- **Shrimp Task Status**: Real-time task completion tracking
- **Milestone Progress**: Major deliverable completion
- **Velocity Metrics**: Team productivity measurement
- **Quality Metrics**: Defect rates e rework indicators

### Adaptive Planning
- **Sprint Retrospectives**: Regular plan adjustment
- **Risk Review**: Emerging risk identification
- **Scope Management**: Change request evaluation
- **Resource Reallocation**: Dynamic team optimization

## Success Metrics

- **Planning Completeness**: All project areas covered (100%)
- **Estimation Accuracy**: Timeline estimates within 20% variance
- **Risk Coverage**: Major risks identified e mitigated (95%)
- **Stakeholder Satisfaction**: Clear communication e alignment
- **Execution Readiness**: Team capability e resource availability

## Report

Al completamento fornisci:
- Path alla project plan directory
- Executive summary con key project parameters
- Detailed timeline con major milestones
- Resource allocation e agent assignment plan
- Risk register con mitigation strategies
- Shrimp task manager setup con initial task backlog
- Next steps per project initiation