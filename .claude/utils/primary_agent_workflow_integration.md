# Primary Agent Workflow Integration - Simplified OpenEvolve

## 🎯 Core Philosophy: Simplicity First

Following official Claude Code documentation approach:
- **Git worktrees** for complete isolation  
- **File-based communication** for robustness
- **Independent instances** for parallel execution
- **No complex coordination** - workflow always continues

## 🔄 Enhanced Development Workflow

### **Standard Workflow:**
```
Primary-Agent → Planner → Coder → Code-Reviewer → Tester-Debugger → Delivery
```

### **With Proactive Optimization:**
```
Primary-Agent → Planner → Coder → [OPTIMIZATION GATE] → Code-Reviewer → Tester-Debugger → Delivery
                                           ↓
                                    [Background Optimization]
```

## 📊 Simple Decision Matrix

### **Automatic Analysis After Code Creation:**

```python
def optimization_decision(code, requirements):
    """Simple, fast decision logic"""
    
    # Calculate basic complexity
    complexity = calculate_complexity(code)
    
    # Check for performance keywords
    perf_required = any(word in requirements.lower() 
                       for word in ["performance", "speed", "optimize", "fast"])
    
    # Detect obvious patterns
    has_nested_loops = "for" in code and code.count("for") > 1
    has_recursion = "def" in code and any(func in code for func in ["factorial", "fibonacci"])
    
    # Decision logic
    if complexity >= 70 or (perf_required and complexity >= 50):
        return "AUTO_OPTIMIZE"
    elif complexity >= 40 and complexity < 70:
        return "ASK_USER"
    else:
        return "SKIP"
```

### **Decision Thresholds:**

| Decision | Conditions | Action |
|----------|-----------|--------|
| **AUTO** | Complexity ≥70 OR Performance required + Complexity ≥50 | Optimize automatically |
| **ASK** | 40 ≤ Complexity < 70 | Quick user consultation |
| **SKIP** | Complexity < 40 | Continue without optimization |

## 🚀 Simplified Execution Flow

### **AUTO-OPTIMIZE Process:**

```bash
# Step 1: Primary Agent creates worktree
git worktree add ../opt-$(date +%s) -b opt-branch

# Step 2: Copy code and context
cp -r ./* ../opt-*/
echo '{"code": "...", "language": "python"}' > ../opt-*/.claude/context.json

# Step 3: Launch optimizer instance
python claude_instance_launcher.py \
  --worktree ../opt-* \
  --task optimize \
  --context .claude/context.json

# Step 4: Continue workflow (don't wait)
# Optimization happens completely independently
```

### **ASK USER Process:**

```
Show simple prompt:
"💡 Optimization opportunity (score: 55/100)
   Estimated: 25% faster, 5 minutes
   Optimize? [Y/n/later]"

If Y: Execute AUTO-OPTIMIZE
If n: Skip and continue
If later: Add to post-delivery tasks
```

## 📁 File Communication Protocol

### **Simple File Structure:**
```
worktree/.claude/
├── context.json          # Input: code + requirements
├── status.json          # Progress updates (every 30s)
├── results.json         # Output: optimized code + metrics  
└── lock                 # File operation safety
```

### **Status Updates (Every 30 seconds):**
```json
{
  "status": "running",
  "progress_percent": 65,
  "current_iteration": 13,
  "best_improvement": 28.5,
  "eta_seconds": 120
}
```

### **Final Results:**
```json
{
  "success": true,
  "original_time_ms": 450,
  "optimized_time_ms": 245,
  "improvement_percent": 45.6,
  "optimized_code": "...",
  "changes": "Replaced O(n²) with O(n log n)"
}
```

## 🔄 Integration Points

### **Simple Integration Logic:**

```python
def integrate_optimization():
    """Check for optimization results at key workflow points"""
    
    # Before Code Review
    if exists("../opt-*/results.json"):
        results = load_results()
        if results.success and results.improvement_percent > 10:
            use_optimized_code()
    
    # Before Testing  
    if new_results_available():
        test_both_versions()
        
    # Before Delivery
    choose_best_validated_version()
    cleanup_old_worktrees()  # > 24 hours old
```

### **Integration Timeline:**

| Workflow Stage | Check for Results | Action if Available |
|---------------|------------------|---------------------|
| Before Review | Yes | Use optimized if validated |
| Before Testing | Yes | Test both versions |
| Before Delivery | Yes | Choose best version |
| After Delivery | Yes | Cleanup worktrees |

## 💬 User Experience

### **Transparent Communication:**

**Auto-Optimization:**
```
✅ Code complete
🔍 High complexity detected
🚀 Background optimization started
   [Workflow continues normally]
   
[Later:]
✅ Optimization ready: 45% faster
```

**User Choice:**
```
💡 Optimization available (25% improvement, 5 min)
   Optimize? [Y/n/later]
```

**Skip:**
```
✅ Code complete - Low complexity
   Proceeding to review
```

## 📈 Success Metrics

### **Simplicity Metrics:**
- Decision time: < 2 seconds
- Worktree setup: < 5 seconds
- No workflow blocking ever
- File operations: < 100ms

### **Quality Metrics:**
- Optimization success rate: > 80%
- Average improvement: > 25%
- User acceptance (when asked): > 70%
- Integration conflicts: < 5%

## 🛠️ Implementation Details

### **Required Components (Already Built):**

1. **Claude Instance Launcher** (`claude_instance_launcher.py`)
   - Spawns independent Claude instances
   - Manages worktree context
   - Returns immediately (fire-and-forget)

2. **Worktree Manager** (`worktree_manager_extended.py`)
   - Creates/manages git worktrees
   - Handles file communication
   - Automatic cleanup after 24 hours

3. **File Communication System**
   - Atomic file operations with locks
   - 5ms average operation time
   - JSON-based simple protocols

### **Workflow Integration Code:**

```python
class SimplifiedOptimizationGate:
    """Minimal integration into Primary Agent workflow"""
    
    def __init__(self):
        self.launcher = ClaudeInstanceLauncher()
        self.worktree_mgr = WorktreeManager()
    
    def should_optimize(self, code, requirements):
        """Quick decision: AUTO/ASK/SKIP"""
        complexity = self.calculate_complexity(code)
        
        if complexity >= 70:
            return "AUTO"
        elif 40 <= complexity < 70:
            return "ASK"
        return "SKIP"
    
    def execute_optimization(self, code, language):
        """Launch background optimization"""
        # Create worktree
        worktree = self.worktree_mgr.create()
        
        # Save context
        context = {"code": code, "language": language}
        save_json(f"{worktree}/.claude/context.json", context)
        
        # Launch optimizer (returns immediately)
        self.launcher.spawn_optimizer(worktree)
        
        # Continue workflow - don't wait
        return worktree
    
    def check_results(self, worktree):
        """Non-blocking check for results"""
        results_file = f"{worktree}/.claude/results.json"
        if os.path.exists(results_file):
            return load_json(results_file)
        return None
```

## 🔒 Robustness Guarantees

1. **Workflow Never Blocked**
   - Optimization is always background
   - Failures don't affect main flow
   - Original code always available

2. **Complete Isolation**
   - Separate git worktrees
   - Independent Claude instances
   - No shared state or services

3. **Simple Fallbacks**
   - If optimization fails: use original
   - If integration conflicts: use original
   - If timeout: use original

4. **Automatic Cleanup**
   - Worktrees deleted after 24 hours
   - No resource accumulation
   - Clean git repository

## 📝 Summary

This simplified approach:
- ✅ Follows official Claude Code docs
- ✅ Uses proven git worktree isolation
- ✅ Implements simple file communication
- ✅ Maintains workflow continuity
- ✅ Provides clear user experience
- ✅ Ensures robustness through simplicity

**Key Principle:** The standard workflow ALWAYS continues. Optimization is a bonus that happens in parallel without any risk or complexity to the main development flow.