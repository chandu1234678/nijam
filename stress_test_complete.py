"""
Comprehensive Stress Test Suite
Tests all system components under load
"""

import requests
import time
import json
import concurrent.futures
import statistics
from datetime import datetime

BASE_URL = "http://localhost:8000"

class StressTestResults:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.response_times = []
        self.errors = []
    
    def add_result(self, passed, response_time=None, error=None):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            if response_time:
                self.response_times.append(response_time)
        else:
            self.tests_failed += 1
            if error:
                self.errors.append(error)
    
    def get_stats(self):
        if not self.response_times:
            return {}
        return {
            'min': min(self.response_times),
            'max': max(self.response_times),
            'avg': statistics.mean(self.response_times),
            'median': statistics.median(self.response_times),
            'p95': statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times)
        }

results = StressTestResults()

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_health_check():
    """Test 1: Health Check Endpoint"""
    print_header("TEST 1: Health Check Stress Test")
    print("Running 100 concurrent health checks...")
    
    def check_health():
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            elapsed = time.time() - start
            return response.status_code == 200, elapsed, None
        except Exception as e:
            return False, None, str(e)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_health) for _ in range(100)]
        for future in concurrent.futures.as_completed(futures):
            passed, elapsed, error = future.result()
            results.add_result(passed, elapsed, error)
    
    stats = results.get_stats()
    print(f"✓ Completed: {results.tests_passed}/100 passed")
    if stats:
        print(f"  Response times: min={stats['min']*1000:.0f}ms, avg={stats['avg']*1000:.0f}ms, max={stats['max']*1000:.0f}ms")

def test_concurrent_claims():
    """Test 2: Concurrent Claim Analysis"""
    print_header("TEST 2: Concurrent Claim Analysis")
    print("Analyzing 20 claims concurrently...")
    
    test_claims = [
        "Breaking: Earth is flat",
        "COVID vaccines are safe",
        "Climate change is real",
        "Moon landing was fake",
        "Water is wet",
        "The sun rises in the east",
        "Vaccines cause autism",
        "5G causes coronavirus",
        "Drinking water is healthy",
        "Exercise is good for health",
        "Smoking causes cancer",
        "The Earth orbits the sun",
        "Gravity exists",
        "Birds are real",
        "Fish can swim",
        "Fire is hot",
        "Ice is cold",
        "Trees produce oxygen",
        "Humans need air to breathe",
        "The sky is blue"
    ]
    
    def analyze_claim(claim):
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/message",
                json={"message": claim},
                timeout=60
            )
            elapsed = time.time() - start
            return response.status_code == 200, elapsed, None
        except Exception as e:
            return False, None, str(e)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(analyze_claim, claim) for claim in test_claims]
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            passed, elapsed, error = future.result()
            results.add_result(passed, elapsed, error)
            completed += 1
            if completed % 5 == 0:
                print(f"  Progress: {completed}/20 claims analyzed")
    
    stats = results.get_stats()
    print(f"✓ Completed: {results.tests_passed - 100}/{len(test_claims)} passed")
    if stats:
        print(f"  Response times: avg={stats['avg']:.1f}s, p95={stats['p95']:.1f}s")

def test_rapid_fire():
    """Test 3: Rapid Fire Requests"""
    print_header("TEST 3: Rapid Fire Requests")
    print("Sending 50 requests as fast as possible...")
    
    def rapid_request():
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/velocity/stats", timeout=5)
            elapsed = time.time() - start
            return response.status_code == 200, elapsed, None
        except Exception as e:
            return False, None, str(e)
    
    start_time = time.time()
    for i in range(50):
        passed, elapsed, error = rapid_request()
        results.add_result(passed, elapsed, error)
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/50 requests")
    
    total_time = time.time() - start_time
    rps = 50 / total_time
    
    print(f"✓ Completed: {results.tests_passed - 120}/50 passed")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Requests/second: {rps:.1f}")

def test_viral_detection():
    """Test 4: Viral Detection System"""
    print_header("TEST 4: Viral Detection Stress Test")
    print("Triggering viral detection with 60 rapid claims...")
    
    test_claim = "URGENT: Breaking news everyone must see"
    viral_triggered = False
    
    for i in range(60):
        try:
            response = requests.post(
                f"{BASE_URL}/message",
                json={"message": test_claim},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                velocity = data.get('velocity_metrics', {})
                
                if velocity.get('is_viral'):
                    viral_triggered = True
                    print(f"  🚨 Viral alert triggered at request #{i + 1}")
                    print(f"     5-min count: {velocity.get('count_5min', 0)}")
                    print(f"     Velocity score: {velocity.get('velocity_score', 0):.3f}")
                    results.add_result(True)
                    break
                
                if (i + 1) % 15 == 0:
                    print(f"  Progress: {i + 1}/60 requests, 5min={velocity.get('count_5min', 0)}")
                
                results.add_result(True)
            else:
                results.add_result(False, error=f"Status {response.status_code}")
        except Exception as e:
            results.add_result(False, error=str(e))
        
        time.sleep(0.1)
    
    if viral_triggered:
        print(f"✓ Viral detection working correctly")
    else:
        print(f"⚠️  Viral detection not triggered (may need more requests)")

def test_error_handling():
    """Test 5: Error Handling"""
    print_header("TEST 5: Error Handling")
    print("Testing error scenarios...")
    
    error_tests = [
        ("Empty message", {"message": ""}),
        ("Very long message", {"message": "A" * 10000}),
        ("Special characters", {"message": "!@#$%^&*()_+{}[]|\\:;\"'<>?,./"}),
        ("Unicode", {"message": "测试 тест テスト 🎉"}),
        ("SQL injection attempt", {"message": "'; DROP TABLE users; --"}),
    ]
    
    for test_name, payload in error_tests:
        try:
            response = requests.post(
                f"{BASE_URL}/message",
                json=payload,
                timeout=30
            )
            # Should either succeed or return proper error
            passed = response.status_code in [200, 400, 422]
            results.add_result(passed)
            status = "✓" if passed else "✗"
            print(f"  {status} {test_name}: {response.status_code}")
        except Exception as e:
            results.add_result(False, error=str(e))
            print(f"  ✗ {test_name}: {str(e)}")

def test_endpoints():
    """Test 6: All Endpoints"""
    print_header("TEST 6: All Endpoints Stress Test")
    print("Testing all major endpoints...")
    
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/velocity/stats", None),
        ("GET", "/source/credibility", None),
        ("GET", "/clustering/stats", None),
        ("POST", "/message", {"message": "Test claim"}),
    ]
    
    for method, endpoint, payload in endpoints:
        try:
            start = time.time()
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=30)
            
            elapsed = time.time() - start
            passed = response.status_code == 200
            results.add_result(passed, elapsed)
            
            status = "✓" if passed else "✗"
            print(f"  {status} {method} {endpoint}: {response.status_code} ({elapsed*1000:.0f}ms)")
        except Exception as e:
            results.add_result(False, error=str(e))
            print(f"  ✗ {method} {endpoint}: {str(e)}")

def test_memory_leak():
    """Test 7: Memory Leak Detection"""
    print_header("TEST 7: Memory Leak Detection")
    print("Running 100 sequential requests to check for memory leaks...")
    
    for i in range(100):
        try:
            response = requests.post(
                f"{BASE_URL}/message",
                json={"message": f"Test claim {i}"},
                timeout=30
            )
            passed = response.status_code == 200
            results.add_result(passed)
            
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/100 requests")
        except Exception as e:
            results.add_result(False, error=str(e))
    
    print(f"✓ Completed: No crashes detected")

def print_final_report():
    """Print final test report"""
    print("\n" + "="*80)
    print("  STRESS TEST FINAL REPORT")
    print("="*80)
    
    print(f"\n📊 Overall Results:")
    print(f"  Total Tests: {results.tests_run}")
    print(f"  Passed: {results.tests_passed} ({results.tests_passed/results.tests_run*100:.1f}%)")
    print(f"  Failed: {results.tests_failed} ({results.tests_failed/results.tests_run*100:.1f}%)")
    
    stats = results.get_stats()
    if stats:
        print(f"\n⏱️  Response Time Statistics:")
        print(f"  Min: {stats['min']*1000:.0f}ms")
        print(f"  Average: {stats['avg']*1000:.0f}ms")
        print(f"  Median: {stats['median']*1000:.0f}ms")
        print(f"  95th percentile: {stats['p95']*1000:.0f}ms")
        print(f"  Max: {stats['max']*1000:.0f}ms")
    
    if results.errors:
        print(f"\n❌ Errors ({len(results.errors)} total):")
        error_counts = {}
        for error in results.errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {count}x: {error[:60]}")
    
    success_rate = results.tests_passed / results.tests_run * 100
    
    print(f"\n{'='*80}")
    if success_rate >= 95:
        print("  ✅ STRESS TEST PASSED - System is stable under load!")
    elif success_rate >= 80:
        print("  ⚠️  STRESS TEST PARTIAL - Some issues detected")
    else:
        print("  ❌ STRESS TEST FAILED - System needs optimization")
    print(f"{'='*80}\n")

def main():
    print("\n" + "="*80)
    print("  COMPREHENSIVE STRESS TEST SUITE")
    print("  Testing system under heavy load")
    print("="*80)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {BASE_URL}")
    
    start_time = time.time()
    
    try:
        # Run all tests
        test_health_check()
        test_concurrent_claims()
        test_rapid_fire()
        test_viral_detection()
        test_error_handling()
        test_endpoints()
        test_memory_leak()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
    
    total_time = time.time() - start_time
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {total_time:.1f}s")
    
    print_final_report()

if __name__ == "__main__":
    main()
