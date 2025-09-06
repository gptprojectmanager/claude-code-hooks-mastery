# Primary Agent Workflow - Simplified OpenEvolve Integration

## 🎯 Philosophy: Keep It Simple (Official Claude Code Approach)

### Core Principle:
```
User Code Request → Analyze Complexity → Decision: Auto/Ask/Skip → Execute
```

## 📋 Enhanced Development Workflow

### **Standard Development Sequence:**
```
Primary-Agent → Planner → Coder → [OPTIMIZATION GATE] → Code-Reviewer → Tester-Debugger → Delivery
```

### **Phase 2.5: PROACTIVE OPTIMIZATION GATE (Simplified)**

#### **1. Automatic Code Analysis (Always Execute):**
```markdown
After code implementation, analyze:
- Lines of code and structure complexity
- Algorithm patterns (O(n²) vs O(n log n))  
- Nested loops and recursion depth
- Performance keywords in requirements
```

#### **2. Simple Decision Matrix:**

**AUTO-OPTIMIZE (No user input):**
- Complexity score ≥ 70/100
- Detected O(n²) with clear O(n log n) alternative
- User mentioned "performance", "speed", "optimize"
- Classic inefficient patterns detected

**ASK USER (Quick consultation):**
- Complexity score 40-69/100  
- Medium improvement potential (20%+)
- Optimization time < 10 minutes

**SKIP (Continue normally):**
- Complexity score < 40/100
- Simple CRUD/configuration code
- No performance requirements

#### **3. Simplified Optimization Execution:**

**For AUTO-OPTIMIZE:**
```bash
# Primary Agent Actions (Current Instance):
1. Create git worktree for isolation:
   git worktree add ../opt-{timestamp} -b optimization-{timestamp}
   
2. Copy current code to worktree:
   cp -r ./* ../opt-{timestamp}/
   
3. Write optimization context:
   echo "{context}" > ../opt-{timestamp}/.claude/optimization_context.json
   
4. Launch new Claude instance:
   claude_instance_launcher.py --worktree ../opt-{timestamp} \
                               --task "optimize" \
                               --context optimization_context.json

5. Continue standard workflow immediately
   (Don't wait for optimization)

# New Claude Instance (Independent):
1. Load context from optimization_context.json
2. Start OpenEvolve/LiteLLM services locally
3. Execute evolutionary optimization
4. Write results to optimization_results.json
5. Update status file every 30 seconds
6. Exit when complete

# Primary Agent (Monitoring):
- Check optimization_status.json periodically
- Integrate results when ready
- Continue workflow regardless
```

**For ASK USER:**
```
Present simple choice:
"💡 Optimization opportunity detected (score: 52/100)
   Potential: ~25% faster | Time: ~5 minutes | Credits: ~15
   Optimize? [Y/n/later]"
   
If YES → Execute AUTO-OPTIMIZE process
If NO → Skip and continue  
If LATER → Add TODO for post-delivery
```

## 📁 File-Based Communication (Simple & Robust)

### **Files Used (All in worktree):**
```
.claude/
├── optimization_context.json    # Initial context from primary
├── optimization_status.json     # Real-time progress (updated every 30s)
├── optimization_results.json    # Final optimized code + metrics
└── optimization.lock            # Thread safety for file operations
```

### **Status File Format:**
```json
{
  "status": "running|complete|failed",
  "progress": 65,
  "current_iteration": 14,
  "total_iterations": 20,
  "best_improvement": 32.5,
  "estimated_remaining": 120,
  "last_updated": "2025-01-13T10:45:23Z"
}
```

### **Results File Format:**
```json
{
  "original_metrics": {
    "complexity": 78,
    "execution_time_ms": 450
  },
  "optimized_metrics": {
    "complexity": 45,
    "execution_time_ms": 245,
    "improvement_percent": 45.6
  },
  "optimized_code": "...",
  "changes_summary": "Replaced nested loops with vectorized operations",
  "validation_passed": true
}
```

## 🔄 Integration Management (Simplified)

### **Integration Points:**
```
Before Code Review:
  if optimization_results.json exists AND validation_passed:
    use optimized_code
  else:
    use original_code

Before Testing:
  if new optimization_results.json available:
    test both versions
    compare results
    
Before Delivery:
  choose best validated version
  cleanup worktree
```

### **Automatic Cleanup:**
```bash
# After 24 hours, automatic cleanup:
find ../opt-* -mtime +1 -exec rm -rf {} \;
```

## 💬 User Communication (Clear & Simple)

### **Auto-Optimization Messages:**
```
✅ Code implemented
🔍 High complexity detected (78/100)
🚀 Starting background optimization...
   [Continue with workflow - optimization runs independently]

[Later, when ready:]
✅ Optimization complete: 45% faster
   Using optimized version for review
```

### **Ask User Messages:**
```
✅ Code implemented  
💡 Optimization available: ~25% improvement (5 min)
   Optimize? [Y/n/later]
```

### **Skip Messages:**
```
✅ Code implemented
✅ Low complexity - proceeding to review
```

## 🎯 Success Criteria

### **Simplicity Metrics:**
- No complex KRAG namespaces
- No inter-instance communication protocols
- No shared background services
- Just: worktrees + files + independent instances

### **Performance Metrics:**
- Optimization decision: < 2 seconds
- Worktree creation: < 5 seconds  
- Instance launch: < 10 seconds
- File communication: < 100ms per operation

### **Quality Gates:**
- Original workflow never blocked
- Optimization failures don't affect delivery
- All file operations are atomic
- Cleanup is automatic

## 📝 Implementation Checklist

**ALREADY IMPLEMENTED:**
- ✅ Claude Instance Launcher (`claude_instance_launcher.py`)
- ✅ Worktree Manager Extended (`worktree_manager_extended.py`)
- ✅ File communication system (5ms operations)
- ✅ Automatic cleanup utilities

**WORKFLOW INTEGRATION:**
- ✅ Simple decision logic (Auto/Ask/Skip)
- ✅ Git worktree isolation
- ✅ Independent instance execution
- ✅ File-based monitoring
- ✅ Seamless result integration

## 🚀 Quick Start Example

```python
# Primary Agent detects complex code:
if complexity_score >= 70:
    # Create worktree
    worktree_path = create_optimization_worktree()
    
    # Write context
    save_optimization_context(worktree_path, code, requirements)
    
    # Launch optimizer (fire and forget)
    launch_optimizer_instance(worktree_path)
    
    # Continue immediately
    proceed_to_code_review(original_code)
    
# Later, check for results:
if optimization_complete():
    optimized = load_optimization_results()
    if optimized.validation_passed:
        use_optimized_code()
```

## 🔒 Robustness Guarantees

1. **Original workflow always continues** - optimization never blocks
2. **Failures are isolated** - worktree problems don't affect main
3. **File locks prevent races** - atomic operations only
4. **Automatic cleanup** - no resource leaks
5. **Simple fallback** - always have working original code

---

**Remember:** This simplified approach follows the official Claude Code documentation philosophy of using git worktrees for isolation and avoiding complex inter-instance communication. Keep it simple, keep it working.