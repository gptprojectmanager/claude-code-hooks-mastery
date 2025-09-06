"""
Performance Tests for GitHub Integration System
Benchmarking, load testing, and performance validation
"""

import pytest
import asyncio
import time
# psutil might not be available in test environment, so make it optional
try:
    import psutil
except ImportError:
    psutil = None
import gc
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from unittest.mock import AsyncMock, MagicMock
from concurrent.futures import ThreadPoolExecutor
import statistics
import sys
from pathlib import Path

# Add parent directories to path for imports
test_dir = Path(__file__).parent.parent
if str(test_dir) not in sys.path:
    sys.path.insert(0, str(test_dir))

try:
    from conftest import TestConfig
except ImportError:
    # Fallback if direct import fails
    from tests.github_integration_suite.conftest import TestConfig


class TestGitHubServicePerformance:
    """Test GitHub Service performance characteristics."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_response_time_benchmarks(
        self,
        mock_github_service,
        performance_thresholds: Dict[str, float]
    ):
        """Test response time meets performance thresholds."""
        operations = [
            'get_repo_info',
            'create_pull_request',
            'list_workflows',
            'get_workflow_runs'
        ]
        
        response_times = {}
        
        async with mock_github_service as github_service:
            for operation in operations:
                times = []
                
                # Perform multiple measurements for statistical reliability
                for _ in range(10):
                    start_time = time.perf_counter()
                    
                    if operation == 'get_repo_info':
                        await github_service.get_repo_info('test-owner/test-repo')
                    elif operation == 'create_pull_request':
                        await github_service.create_pull_request({
                            'title': 'Test PR',
                            'head': 'feature',
                            'base': 'main',
                            'body': 'Test description'
                        })
                    elif operation == 'list_workflows':
                        await github_service.list_workflows('test-owner/test-repo')
                    elif operation == 'get_workflow_runs':
                        await github_service.get_workflow_runs('test-owner/test-repo', 123)
                    
                    end_time = time.perf_counter()
                    times.append(end_time - start_time)
                
                response_times[operation] = {
                    'mean': statistics.mean(times),
                    'median': statistics.median(times),
                    'max': max(times),
                    'min': min(times),
                    'stdev': statistics.stdev(times) if len(times) > 1 else 0.0
                }
        
        # Verify all operations meet response time thresholds
        max_response_time = performance_thresholds['max_response_time']
        for operation, metrics in response_times.items():
            assert metrics['mean'] < max_response_time, (
                f"{operation} mean response time {metrics['mean']:.3f}s "
                f"exceeds threshold {max_response_time}s"
            )
            assert metrics['max'] < max_response_time * 1.5, (
                f"{operation} max response time {metrics['max']:.3f}s "
                f"exceeds threshold {max_response_time * 1.5}s"
            )
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_throughput_validation(
        self,
        mock_github_service,
        performance_thresholds: Dict[str, float]
    ):
        """Test system throughput meets minimum requirements."""
        min_throughput = performance_thresholds['min_throughput']  # requests per minute
        test_duration = 10  # seconds
        
        request_count = 0
        start_time = time.perf_counter()
        end_time = start_time + test_duration
        
        async def make_test_request():
            nonlocal request_count
            async with mock_github_service as github_service:
                await github_service.get_repo_info('test-owner/test-repo')
                request_count += 1
        
        # Generate concurrent requests for the test duration
        tasks = []
        while time.perf_counter() < end_time:
            # Create batches of concurrent requests
            batch_size = 10
            batch_tasks = [make_test_request() for _ in range(batch_size)]
            tasks.extend(batch_tasks)
            
            # Wait for batch to complete
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Brief pause to avoid overwhelming the system
            await asyncio.sleep(0.1)
        
        actual_duration = time.perf_counter() - start_time
        actual_throughput = (request_count / actual_duration) * 60  # requests per minute
        
        assert actual_throughput >= min_throughput, (
            f"Throughput {actual_throughput:.1f} req/min below threshold {min_throughput} req/min"
        )
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.skipif(psutil is None, reason="psutil not available for memory monitoring")
    async def test_memory_usage_monitoring(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        performance_thresholds: Dict[str, float]
    ):
        """Test memory usage stays within acceptable limits."""
        max_memory_mb = performance_thresholds['max_memory_usage']
        
        # Get baseline memory usage
        gc.collect()  # Force garbage collection
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = []
        
        async def memory_intensive_workflow():
            """Simulate memory-intensive GitHub operations."""
            async with mock_github_service as github_service:
                async with mock_primary_controller as controller:
                    # Perform multiple operations that could accumulate memory
                    for i in range(100):
                        # Repository analysis operation
                        await controller.delegate_github_task({
                            'operation': 'repository_analysis',
                            'repo': f'test-owner/repo-{i}',
                            'parameters': {'detailed': True}
                        })
                        
                        # Event bus operations
                        await mock_event_bus.publish_event('test_event', {
                            'data': f'large_payload_{i}',
                            'timestamp': datetime.utcnow().isoformat(),
                            'metadata': {'size': 'large'} * 100  # Simulate large payload
                        })
                        
                        # Sample memory usage periodically
                        if i % 10 == 0:
                            current_memory = process.memory_info().rss / 1024 / 1024
                            memory_samples.append(current_memory - baseline_memory)
        
        # Execute memory-intensive workflow
        await memory_intensive_workflow()
        
        # Final memory check
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        peak_additional_memory = max(memory_samples) if memory_samples else 0
        final_additional_memory = final_memory - baseline_memory
        
        assert peak_additional_memory < max_memory_mb, (
            f"Peak memory usage {peak_additional_memory:.1f}MB exceeds threshold {max_memory_mb}MB"
        )
        assert final_additional_memory < max_memory_mb * 0.8, (
            f"Final memory usage {final_additional_memory:.1f}MB suggests memory leaks"
        )
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_operation_performance(
        self,
        mock_github_service,
        mock_primary_controller,
        performance_thresholds: Dict[str, float]
    ):
        """Test performance under concurrent load."""
        max_response_time = performance_thresholds['max_response_time']
        concurrency_levels = [1, 5, 10, 20]
        
        performance_results = {}
        
        for concurrency in concurrency_levels:
            operation_times = []
            
            async def concurrent_operation():
                start_time = time.perf_counter()
                
                async with mock_primary_controller as controller:
                    result = await controller.delegate_github_task({
                        'operation': 'repository_analysis',
                        'parameters': {'detailed': True}
                    })
                    assert result['success'] is True
                
                end_time = time.perf_counter()
                return end_time - start_time
            
            # Execute concurrent operations
            tasks = [concurrent_operation() for _ in range(concurrency)]
            times = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and collect valid times
            valid_times = [t for t in times if isinstance(t, (int, float))]
            
            if valid_times:
                performance_results[concurrency] = {
                    'mean_time': statistics.mean(valid_times),
                    'max_time': max(valid_times),
                    'successful_operations': len(valid_times),
                    'failed_operations': len(times) - len(valid_times)
                }
        
        # Verify performance scaling
        for concurrency, metrics in performance_results.items():
            success_rate = metrics['successful_operations'] / concurrency * 100
            
            # All operations should complete successfully
            assert success_rate >= performance_thresholds['min_success_rate'], (
                f"Success rate {success_rate:.1f}% at concurrency {concurrency} "
                f"below threshold {performance_thresholds['min_success_rate']}%"
            )
            
            # Response times should remain reasonable under load
            max_acceptable_time = max_response_time * (1 + concurrency * 0.1)  # Allow degradation
            assert metrics['max_time'] < max_acceptable_time, (
                f"Max response time {metrics['max_time']:.3f}s at concurrency {concurrency} "
                f"exceeds acceptable limit {max_acceptable_time:.3f}s"
            )


class TestEventBusPerformance:
    """Test Event Bus performance characteristics."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_event_publishing_performance(
        self,
        mock_event_bus,
        performance_thresholds: Dict[str, float]
    ):
        """Test event publishing performance and scalability."""
        max_response_time = performance_thresholds['max_response_time']
        event_counts = [10, 100, 500, 1000]
        
        performance_metrics = {}
        
        for event_count in event_counts:
            publish_times = []
            
            # Test batch event publishing
            start_time = time.perf_counter()
            
            publish_tasks = []
            for i in range(event_count):
                event_data = {
                    'event_id': f'test-event-{i}',
                    'data': f'test-data-{i}',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                task = mock_event_bus.publish_event(
                    f'test_event_type_{i % 10}',  # Distribute across event types
                    event_data
                )
                publish_tasks.append(task)
            
            # Execute all publishing operations
            results = await asyncio.gather(*publish_tasks, return_exceptions=True)
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            successful_publishes = len([r for r in results if not isinstance(r, Exception)])
            
            performance_metrics[event_count] = {
                'total_time': total_time,
                'successful_publishes': successful_publishes,
                'average_time_per_event': total_time / event_count,
                'events_per_second': event_count / total_time
            }
        
        # Verify performance thresholds
        for event_count, metrics in performance_metrics.items():
            # Average time per event should remain reasonable
            assert metrics['average_time_per_event'] < max_response_time / 10, (
                f"Average event publish time {metrics['average_time_per_event']:.4f}s "
                f"exceeds threshold for {event_count} events"
            )
            
            # Should maintain high success rate
            success_rate = metrics['successful_publishes'] / event_count * 100
            assert success_rate >= 95, (
                f"Event publish success rate {success_rate:.1f}% below 95% for {event_count} events"
            )
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_subscription_management_performance(
        self,
        mock_event_bus,
        performance_thresholds: Dict[str, float]
    ):
        """Test performance of subscription management operations."""
        max_response_time = performance_thresholds['max_response_time']
        
        # Test subscription creation performance
        subscription_times = []
        subscription_ids = []
        
        for i in range(100):
            start_time = time.perf_counter()
            
            subscription_id = mock_event_bus.subscribe_handler(
                f'test_event_type_{i % 20}',
                lambda event_data: None,  # Mock handler
                priority=i % 3
            )
            
            end_time = time.perf_counter()
            subscription_times.append(end_time - start_time)
            subscription_ids.append(subscription_id)
        
        # Verify subscription creation performance
        avg_subscription_time = statistics.mean(subscription_times)
        assert avg_subscription_time < max_response_time / 100, (
            f"Average subscription time {avg_subscription_time:.4f}s exceeds threshold"
        )
        
        # Test subscription removal performance
        unsubscribe_times = []
        
        for subscription_id in subscription_ids:
            start_time = time.perf_counter()
            
            result = mock_event_bus.unsubscribe_handler(subscription_id)
            
            end_time = time.perf_counter()
            unsubscribe_times.append(end_time - start_time)
        
        avg_unsubscribe_time = statistics.mean(unsubscribe_times)
        assert avg_unsubscribe_time < max_response_time / 100, (
            f"Average unsubscribe time {avg_unsubscribe_time:.4f}s exceeds threshold"
        )


class TestLoadTesting:
    """Load testing and stress testing scenarios."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_load_handling(
        self,
        mock_github_service,
        mock_event_bus,
        mock_primary_controller,
        performance_thresholds: Dict[str, float]
    ):
        """Test system behavior under sustained high load."""
        min_throughput = performance_thresholds['min_throughput']
        max_response_time = performance_thresholds['max_response_time']
        
        # Sustained load parameters
        load_duration = 30  # seconds
        target_rps = 50  # requests per second
        
        successful_operations = 0
        failed_operations = 0
        response_times = []
        start_time = time.perf_counter()
        
        async def load_operation():
            nonlocal successful_operations, failed_operations
            
            operation_start = time.perf_counter()
            
            try:
                async with mock_primary_controller as controller:
                    result = await controller.delegate_github_task({
                        'operation': 'repository_analysis',
                        'parameters': {'load_test': True}
                    })
                    
                    if result.get('success'):
                        successful_operations += 1
                    else:
                        failed_operations += 1
                        
            except Exception:
                failed_operations += 1
            
            operation_end = time.perf_counter()
            response_times.append(operation_end - operation_start)
        
        # Generate sustained load
        while time.perf_counter() - start_time < load_duration:
            # Create batch of operations
            batch_size = 5
            batch_tasks = [load_operation() for _ in range(batch_size)]
            
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Control request rate
            await asyncio.sleep(batch_size / target_rps)
        
        total_duration = time.perf_counter() - start_time
        total_operations = successful_operations + failed_operations
        actual_throughput = (successful_operations / total_duration) * 60  # requests per minute
        
        # Performance validation
        assert actual_throughput >= min_throughput * 0.8, (
            f"Sustained load throughput {actual_throughput:.1f} req/min "
            f"below 80% of threshold {min_throughput} req/min"
        )
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            
            assert avg_response_time < max_response_time, (
                f"Average response time {avg_response_time:.3f}s under sustained load "
                f"exceeds threshold {max_response_time}s"
            )
            
            assert p95_response_time < max_response_time * 2, (
                f"95th percentile response time {p95_response_time:.3f}s "
                f"exceeds acceptable limit {max_response_time * 2}s"
            )
        
        # Error rate validation
        error_rate = (failed_operations / total_operations) * 100 if total_operations > 0 else 0
        max_error_rate = performance_thresholds['max_error_rate']
        
        assert error_rate <= max_error_rate, (
            f"Error rate {error_rate:.1f}% under sustained load "
            f"exceeds threshold {max_error_rate}%"
        )
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_spike_load_resilience(
        self,
        mock_github_service,
        mock_primary_controller,
        performance_thresholds: Dict[str, float]
    ):
        """Test system resilience to sudden load spikes."""
        max_response_time = performance_thresholds['max_response_time']
        
        # Baseline load
        baseline_operations = 10
        spike_operations = 100
        
        performance_data = {
            'baseline': {'times': [], 'success_count': 0, 'failure_count': 0},
            'spike': {'times': [], 'success_count': 0, 'failure_count': 0},
            'recovery': {'times': [], 'success_count': 0, 'failure_count': 0}
        }
        
        async def execute_operation_batch(batch_size: int, phase: str):
            async def single_operation():
                operation_start = time.perf_counter()
                
                try:
                    async with mock_primary_controller as controller:
                        result = await controller.delegate_github_task({
                            'operation': 'repository_analysis',
                            'parameters': {'phase': phase}
                        })
                        
                        operation_end = time.perf_counter()
                        response_time = operation_end - operation_start
                        performance_data[phase]['times'].append(response_time)
                        
                        if result.get('success'):
                            performance_data[phase]['success_count'] += 1
                        else:
                            performance_data[phase]['failure_count'] += 1
                            
                except Exception:
                    operation_end = time.perf_counter()
                    response_time = operation_end - operation_start
                    performance_data[phase]['times'].append(response_time)
                    performance_data[phase]['failure_count'] += 1
            
            # Execute batch concurrently
            tasks = [single_operation() for _ in range(batch_size)]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Phase 1: Baseline load
        await execute_operation_batch(baseline_operations, 'baseline')
        
        # Phase 2: Spike load
        await execute_operation_batch(spike_operations, 'spike')
        
        # Phase 3: Recovery validation
        await asyncio.sleep(1)  # Brief recovery period
        await execute_operation_batch(baseline_operations, 'recovery')
        
        # Validate baseline performance
        baseline_avg = statistics.mean(performance_data['baseline']['times'])
        assert baseline_avg < max_response_time, (
            f"Baseline response time {baseline_avg:.3f}s exceeds threshold"
        )
        
        # Validate spike handling
        spike_avg = statistics.mean(performance_data['spike']['times'])
        spike_max = max(performance_data['spike']['times'])
        
        # Allow degradation during spike, but within bounds
        acceptable_spike_avg = max_response_time * 3
        acceptable_spike_max = max_response_time * 5
        
        assert spike_avg < acceptable_spike_avg, (
            f"Spike average response time {spike_avg:.3f}s "
            f"exceeds acceptable degradation {acceptable_spike_avg:.3f}s"
        )
        
        assert spike_max < acceptable_spike_max, (
            f"Spike max response time {spike_max:.3f}s "
            f"exceeds acceptable limit {acceptable_spike_max:.3f}s"
        )
        
        # Validate recovery
        recovery_avg = statistics.mean(performance_data['recovery']['times'])
        recovery_degradation = recovery_avg / baseline_avg
        
        assert recovery_degradation < 1.5, (
            f"Recovery performance degradation {recovery_degradation:.2f}x "
            f"suggests system hasn't fully recovered"
        )


class TestRateLimitingPerformance:
    """Test rate limiting behavior and performance impact."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_rate_limit_compliance(
        self,
        mock_github_service,
        performance_thresholds: Dict[str, float]
    ):
        """Test rate limiting compliance and performance impact."""
        # Configure rate limiting scenario
        rate_limit_requests = 10  # requests per window
        rate_limit_window = 5     # seconds
        
        request_timestamps = []
        successful_requests = 0
        rate_limited_requests = 0
        
        async def rate_limited_operation():
            nonlocal successful_requests, rate_limited_requests
            
            request_time = time.perf_counter()
            request_timestamps.append(request_time)
            
            try:
                async with mock_github_service as github_service:
                    # Simulate rate limiting behavior
                    current_window_requests = len([
                        ts for ts in request_timestamps 
                        if request_time - ts <= rate_limit_window
                    ])
                    
                    if current_window_requests > rate_limit_requests:
                        rate_limited_requests += 1
                        raise Exception("Rate limit exceeded")
                    
                    await github_service.get_repo_info('test-owner/test-repo')
                    successful_requests += 1
                    
            except Exception:
                rate_limited_requests += 1
        
        # Execute requests that will trigger rate limiting
        total_requests = rate_limit_requests * 3  # Exceed rate limit
        
        tasks = [rate_limited_operation() for _ in range(total_requests)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Validate rate limiting behavior
        total_operations = successful_requests + rate_limited_requests
        rate_limit_effectiveness = rate_limited_requests / total_operations * 100
        
        # Should have rate limited some requests
        assert rate_limit_effectiveness > 0, "Rate limiting not working"
        assert rate_limit_effectiveness < 80, "Rate limiting too aggressive"
        
        # Successful requests should still meet performance thresholds
        success_rate = successful_requests / total_operations * 100
        min_success_rate = performance_thresholds['min_success_rate']
        
        # Adjust expectation for rate limiting scenario
        expected_success_rate = min(min_success_rate, 50)  # Rate limiting will reduce success
        assert success_rate >= expected_success_rate, (
            f"Success rate {success_rate:.1f}% with rate limiting "
            f"below expected {expected_success_rate:.1f}%"
        )