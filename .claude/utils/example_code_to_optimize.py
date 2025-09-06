#!/usr/bin/env python3
"""
Example code for Claude Instance Launcher optimization testing.
This code intentionally contains various optimization opportunities.
"""

import time
import math
from typing import List, Dict, Any


class DataProcessor:
    """A data processor with optimization opportunities."""
    
    def __init__(self, data: List[int]):
        self.data = data
        self.cache = {}
    
    def slow_sort_and_filter(self, threshold: int = 50) -> List[int]:
        """Inefficient sorting and filtering method."""
        # Inefficient nested loops
        result = []
        for i in range(len(self.data)):
            for j in range(len(self.data)):
                if i != j and self.data[i] > self.data[j]:
                    # Bubble sort logic (very inefficient)
                    pass
        
        # Sort using inefficient bubble sort
        sorted_data = self.data.copy()
        for i in range(len(sorted_data)):
            for j in range(0, len(sorted_data) - i - 1):
                if sorted_data[j] > sorted_data[j + 1]:
                    sorted_data[j], sorted_data[j + 1] = sorted_data[j + 1], sorted_data[j]
        
        # Inefficient filtering
        filtered_result = []
        for item in sorted_data:
            if item > threshold:
                filtered_result.append(item)
        
        return filtered_result
    
    def calculate_stats(self, numbers: List[int]) -> Dict[str, float]:
        """Calculate statistics with room for optimization."""
        if not numbers:
            return {}
        
        # Inefficient sum calculation
        total = 0
        for num in numbers:
            total += num
        
        # Inefficient mean calculation
        mean = total / len(numbers)
        
        # Inefficient variance calculation
        variance_sum = 0
        for num in numbers:
            variance_sum += (num - mean) ** 2
        variance = variance_sum / len(numbers)
        
        # Inefficient standard deviation
        std_dev = math.sqrt(variance)
        
        # Inefficient min/max finding
        minimum = numbers[0]
        maximum = numbers[0]
        for num in numbers:
            if num < minimum:
                minimum = num
            if num > maximum:
                maximum = num
        
        return {
            'count': len(numbers),
            'sum': total,
            'mean': mean,
            'variance': variance,
            'std_dev': std_dev,
            'min': minimum,
            'max': maximum
        }
    
    def process_data_chunks(self, chunk_size: int = 10) -> List[Dict[str, Any]]:
        """Process data in chunks with optimization potential."""
        results = []
        
        # Inefficient chunking
        chunks = []
        for i in range(0, len(self.data), chunk_size):
            chunk = []
            for j in range(i, min(i + chunk_size, len(self.data))):
                chunk.append(self.data[j])
            chunks.append(chunk)
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            # Simulate some processing time
            time.sleep(0.001)  # This could be optimized away
            
            # Calculate stats for chunk
            stats = self.calculate_stats(chunk)
            
            # Add chunk metadata
            chunk_info = {
                'chunk_id': i,
                'chunk_size': len(chunk),
                'stats': stats,
                'processed_at': time.time()
            }
            
            results.append(chunk_info)
        
        return results
    
    def find_patterns(self, pattern_length: int = 3) -> List[List[int]]:
        """Find patterns in data - has algorithmic optimization opportunities."""
        patterns = []
        
        # Inefficient pattern detection
        for i in range(len(self.data) - pattern_length + 1):
            current_pattern = []
            for j in range(pattern_length):
                current_pattern.append(self.data[i + j])
            
            # Check if this pattern appears elsewhere
            pattern_count = 0
            for k in range(len(self.data) - pattern_length + 1):
                if k != i:
                    match = True
                    for l in range(pattern_length):
                        if self.data[k + l] != current_pattern[l]:
                            match = False
                            break
                    if match:
                        pattern_count += 1
            
            # Only add if pattern appears more than once
            if pattern_count > 0:
                # Check if we already have this pattern
                pattern_exists = False
                for existing_pattern in patterns:
                    if len(existing_pattern) == len(current_pattern):
                        same = True
                        for m in range(len(current_pattern)):
                            if existing_pattern[m] != current_pattern[m]:
                                same = False
                                break
                        if same:
                            pattern_exists = True
                            break
                
                if not pattern_exists:
                    patterns.append(current_pattern)
        
        return patterns


def demonstrate_usage():
    """Demonstrate the DataProcessor with various optimization opportunities."""
    
    # Generate test data
    test_data = list(range(100, 0, -1))  # Reverse sorted for worst-case scenarios
    test_data.extend([50, 75, 25, 60, 80, 30])  # Add some duplicates and variety
    
    processor = DataProcessor(test_data)
    
    print("=== DataProcessor Optimization Demo ===")
    
    # Test slow sorting and filtering
    print("\n1. Testing slow_sort_and_filter...")
    start_time = time.time()
    filtered_data = processor.slow_sort_and_filter(threshold=50)
    sort_time = time.time() - start_time
    print(f"   Sorted and filtered {len(test_data)} items in {sort_time:.4f} seconds")
    print(f"   Result: {len(filtered_data)} items above threshold")
    
    # Test stats calculation
    print("\n2. Testing calculate_stats...")
    start_time = time.time()
    stats = processor.calculate_stats(test_data)
    stats_time = time.time() - start_time
    print(f"   Calculated stats in {stats_time:.4f} seconds")
    print(f"   Mean: {stats.get('mean', 0):.2f}, StdDev: {stats.get('std_dev', 0):.2f}")
    
    # Test chunk processing
    print("\n3. Testing process_data_chunks...")
    start_time = time.time()
    chunks = processor.process_data_chunks(chunk_size=15)
    chunk_time = time.time() - start_time
    print(f"   Processed {len(chunks)} chunks in {chunk_time:.4f} seconds")
    
    # Test pattern finding
    print("\n4. Testing find_patterns...")
    start_time = time.time()
    patterns = processor.find_patterns(pattern_length=3)
    pattern_time = time.time() - start_time
    print(f"   Found {len(patterns)} patterns in {pattern_time:.4f} seconds")
    
    total_time = sort_time + stats_time + chunk_time + pattern_time
    print(f"\n   Total execution time: {total_time:.4f} seconds")
    print("\n=== Optimization Opportunities ===")
    print("- Replace bubble sort with built-in sort() or sorted()")
    print("- Use list comprehensions instead of manual loops")
    print("- Utilize NumPy for statistical calculations")
    print("- Cache repeated calculations")
    print("- Use built-in min()/max() functions")
    print("- Optimize pattern detection algorithm")
    print("- Remove unnecessary time.sleep() calls")
    print("- Use more efficient data structures")


if __name__ == "__main__":
    demonstrate_usage()