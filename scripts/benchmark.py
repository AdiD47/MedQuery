"""
Performance benchmark script for MedQuery system.
Tests query latency, memory usage, and throughput.
"""

import time
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def benchmark_query():
    """Benchmark a single query execution."""
    from app.crew import run_query
    
    test_query = "What are the top unmet needs in respiratory medicine?"
    
    print("=" * 60)
    print("MedQuery Performance Benchmark")
    print("=" * 60)
    
    # Warmup run
    print("\n[1/3] Warmup run (initializing models)...")
    start = time.time()
    try:
        run_query(test_query)
        warmup_time = time.time() - start
        print(f"✓ Warmup completed in {warmup_time:.2f}s")
    except Exception as e:
        print(f"✗ Warmup failed: {e}")
        return
    
    # Timed runs
    print("\n[2/3] Running 3 timed queries...")
    times = []
    for i in range(3):
        start = time.time()
        try:
            result = run_query(test_query)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Query {i+1}: {elapsed:.2f}s ({len(result['ranked'])} diseases)")
        except Exception as e:
            print(f"  Query {i+1} failed: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n[3/3] Performance Summary:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Min:     {min_time:.2f}s")
        print(f"  Max:     {max_time:.2f}s")
        print(f"  Speedup: {warmup_time / avg_time:.1f}x (cold vs warm)")
        
        # Performance rating
        if avg_time < 5:
            rating = "⚡ EXCELLENT"
        elif avg_time < 10:
            rating = "✓ GOOD"
        elif avg_time < 15:
            rating = "⚠ FAIR"
        else:
            rating = "✗ SLOW"
        
        print(f"  Rating:  {rating}")
        
        # Optimization suggestions
        print(f"\n💡 Optimization Tips:")
        if warmup_time > avg_time * 2:
            print("  • Lazy loading is working (2x speedup after warmup)")
        
        try:
            import numpy
            print("  • NumPy vectorization: ENABLED ✓")
        except ImportError:
            print("  • NumPy vectorization: DISABLED (install with: pip install numpy)")
        
        cache_enabled = os.getenv("ENABLE_CACHING", "true").lower() == "true"
        print(f"  • LRU caching: {'ENABLED ✓' if cache_enabled else 'DISABLED'}")
        
        print("\n" + "=" * 60)

def benchmark_memory():
    """Benchmark memory usage."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        baseline = process.memory_info().rss / 1024**2
        print(f"\nMemory Usage:")
        print(f"  Baseline: {baseline:.0f}MB")
        
        # After import
        from app.crew import run_query
        after_import = process.memory_info().rss / 1024**2
        print(f"  After import: {after_import:.0f}MB (+{after_import - baseline:.0f}MB)")
        
        # After query
        run_query("test query for memory benchmark")
        after_query = process.memory_info().rss / 1024**2
        print(f"  After query: {after_query:.0f}MB (+{after_query - after_import:.0f}MB)")
        
        if after_query < 3000:
            print(f"  Memory efficiency: ✓ GOOD")
        else:
            print(f"  Memory efficiency: ⚠ HIGH (consider reducing MAX_WORKERS)")
            
    except ImportError:
        print("\n⚠ Install psutil for memory profiling: pip install psutil")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark MedQuery performance")
    parser.add_argument("--memory", action="store_true", help="Include memory profiling")
    parser.add_argument("--quick", action="store_true", help="Quick test (1 query)")
    
    args = parser.parse_args()
    
    try:
        if args.memory:
            benchmark_memory()
        
        if not args.quick:
            benchmark_query()
        else:
            print("Quick benchmark mode - running single query...")
            from app.crew import run_query
            start = time.time()
            result = run_query("What are opportunities in cardiovascular disease?")
            elapsed = time.time() - start
            print(f"\n✓ Query completed in {elapsed:.2f}s")
            print(f"  Found {len(result['ranked'])} diseases")
            
    except KeyboardInterrupt:
        print("\n\n⚠ Benchmark interrupted by user")
    except Exception as e:
        print(f"\n✗ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
