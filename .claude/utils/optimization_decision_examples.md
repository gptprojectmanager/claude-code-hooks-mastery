# Optimization Decision Examples - Primary Agent Intelligence

## 🎯 Esempi Pratici della Decision Logic

### **AUTOMATIC Optimization (No user input)**

#### Example 1: Fibonacci Ricorsivo
```python
def fibonacci(n):
    if n <= 1: return n
    return fibonacci(n-1) + fibonacci(n-2)  # O(2^n) - DISASTER!
```
**Primary Agent Decision:** 
- ✅ **AUTO-OPTIMIZE** (Complexity: 95/100)
- Rationale: "Classic exponential algorithm - clear O(n) memoization opportunity"
- Action: Immediate delegation to openevolve-optimizer-opus

#### Example 2: Nested Loop Inefficiency  
```python
def find_duplicates(list1, list2):
    duplicates = []
    for item1 in list1:           # O(n)
        for item2 in list2:       # O(m) -> O(n*m) total
            if item1 == item2:
                duplicates.append(item1)
    return duplicates
```
**Primary Agent Decision:**
- ✅ **AUTO-OPTIMIZE** (Complexity: 82/100) 
- Rationale: "Nested loops with set() opportunity - O(n*m) → O(n+m)"
- Action: Background optimization while continuing workflow

### **CONSULTATIVE Optimization (Ask user)**

#### Example 3: Sorting with Additional Logic
```python
def process_data(data):
    # Sort data first
    sorted_data = sorted(data, key=lambda x: x.value)  # O(n log n)
    
    # Filter and transform - medium complexity
    result = []
    for item in sorted_data:
        if item.value > threshold:
            processed = complex_transform(item)  # Complexity unknown
            result.append(processed)
    
    return result
```
**Primary Agent Decision:**
- ❓ **ASK-USER** (Complexity: 55/100)
- Message: "Medium complexity with 25% potential improvement. Sort+filter could be optimized. Proceed? [Y/n/later]"

#### Example 4: Database Processing Loop  
```python
def update_records(records):
    for record in records:        # Could be optimized with batch operations
        result = database.update(record)
        if result.error:
            handle_error(record, result)
        else:
            log_success(record)
```
**Primary Agent Decision:**
- ❓ **ASK-USER** (Complexity: 48/100)
- Message: "Database loop detected - batch optimization possible. Time: ~3min, Credits: ~12. Optimize? [Y/n]"

### **SKIP Optimization (Continue workflow)**

#### Example 5: Simple CRUD API
```python
@app.post("/users")
def create_user(user_data: UserCreate):
    user = User(**user_data.dict())
    db.session.add(user)
    db.session.commit()
    return user
```
**Primary Agent Decision:**
- ⏭️ **SKIP** (Complexity: 15/100)
- Rationale: "Simple CRUD operation - no algorithmic optimization needed"
- Action: Continue directly to code review

#### Example 6: Configuration Loading
```python
def load_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config
```
**Primary Agent Decision:**
- ⏭️ **SKIP** (Complexity: 8/100) 
- Rationale: "One-time configuration loading - optimization not beneficial"
- Action: Proceed to standard workflow

## 🔄 Workflow Integration Examples

### **Background Optimization Success**
```
1. User requests: "Create a function to find common elements in two lists"
2. Planner: Designs approach
3. Python-Pro-Sonnet: Implements nested loop solution
4. Primary Agent Analysis: 
   ✅ AUTO-OPTIMIZE detected (nested loops, O(n*m))
   🔧 Creating git worktree optimization_workspace_20250813_143522
   🤖 Delegating to openevolve-optimizer-opus in background
5. Code-Reviewer: Reviews original implementation  
6. OpenEvolve completes: O(n*m) → O(n+m) with set intersection
7. Integration: Replace with optimized version (43% performance improvement)
8. Tester-Debugger: Tests optimized version
9. Delivery: Optimized solution with performance metrics
```

### **User Consultation Success**
```
1. User: "Build a data processing pipeline for CSV files"
2. Data-Engineer: Implements pandas-based processing
3. Primary Agent Analysis:
   ❓ CONSULTATIVE (Complexity: 61/100, potential: ~30% improvement)
   💬 "Medium complexity data pipeline with vectorization opportunities. 
       Estimated 6 minutes, 22 credits. Optimize now? [Y/n/later]"
4. User: "Y" 
5. Parallel optimization while code review continues
6. Integration of optimized pipeline with vectorized operations
7. Result: 34% faster processing + maintained readability
```

### **Skip Decision Wisdom**
```  
1. User: "Add user authentication middleware"
2. Security-Specialist: Implements JWT middleware
3. Primary Agent Analysis:
   ⏭️ SKIP (Complexity: 22/100, security code - different optimization needs)
   📝 "Security middleware - optimization not recommended (focus on security audit)"
4. Direct to Security-Auditor for security review instead
5. Result: Secure, well-reviewed middleware without unnecessary optimization
```

## 📊 Learning Examples

### **Pattern Recognition Improvement**
```
Session 1: Manual fibonacci → AUTO-OPTIMIZE → 89% improvement
Session 5: Similar recursive pattern → AUTO-OPTIMIZE (learned)
Session 12: Different recursive algorithm → AUTO-OPTIMIZE (pattern generalization)

Result: Primary Agent learns to recognize recursive inefficiencies across contexts
```

### **User Preference Learning**
```
User A: Always says "Y" to consultative optimization → Learn preference
User B: Usually says "later" → Adjust threshold for asking
User C: Performance-focused projects → Lower consultation threshold

Result: Personalized optimization decision thresholds per user/project
```

## 🎯 Success Metrics Examples

### **Before Proactive Integration:**
- Optimization Rate: 5% (only when explicitly requested)
- Average Improvement: 45% (high-value cases only)
- User Satisfaction: High but infrequent

### **After Proactive Integration:**
- Optimization Rate: 35% (automatic + consultative)  
- Average Improvement: 32% (broader scope, still valuable)
- User Satisfaction: Higher (proactive value delivery)
- Development Time: +8% (but 32% faster code execution)
- Credit Usage: +40% (but higher ROI through systematic optimization)