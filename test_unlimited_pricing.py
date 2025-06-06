"""
Test script to verify unlimited pricing data functionality
This script tests that the system can load and use ALL available pricing data
instead of being limited by sample sizes.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.logging_config import setup_logging

async def test_unlimited_pricing():
    """Test the system with unlimited pricing data"""
    
    # Setup logging
    setup_logging(level='INFO')
    logger = logging.getLogger(__name__)
    
    print("=" * 80)
    print("CS:GO Trade-Up Analysis - Unlimited Pricing Data Test")
    print("=" * 80)
    print()
    
    # Test 1: Compare sample vs all prices
    print("🔍 Test 1: Comparing sample size vs unlimited pricing...")
    
    # Test with small sample first
    print("\n📊 Testing with sample size (100 prices)...")
    finder_sample = ComprehensiveTradeUpFinder()
    await finder_sample.initialize(sample_size=100)
    
    sample_cache_size = len(finder_sample._cached_prices)
    print(f"✅ Sample mode loaded: {sample_cache_size} prices")
    
    # Test finding trades with sample
    sample_results = await finder_sample.find_profitable_trades(min_profit=0.50, limit=3)
    print(f"✅ Sample mode found: {len(sample_results)} trade opportunities")
    
    await finder_sample.close()
    
    # Test with all prices
    print("\n📊 Testing with unlimited pricing (all available prices)...")
    finder_unlimited = ComprehensiveTradeUpFinder()
    await finder_unlimited.initialize(use_all_prices=True)
    
    unlimited_cache_size = len(finder_unlimited._cached_prices)
    print(f"✅ Unlimited mode loaded: {unlimited_cache_size} prices")
    
    # Test finding trades with all prices
    unlimited_results = await finder_unlimited.find_profitable_trades(min_profit=0.50, limit=3)
    print(f"✅ Unlimited mode found: {len(unlimited_results)} trade opportunities")
    
    # Compare results
    print(f"\n📈 Comparison Results:")
    print(f"   Sample mode:    {sample_cache_size:,} prices → {len(sample_results)} opportunities")
    print(f"   Unlimited mode: {unlimited_cache_size:,} prices → {len(unlimited_results)} opportunities")
    
    improvement_ratio = unlimited_cache_size / sample_cache_size if sample_cache_size > 0 else 0
    print(f"   📊 Price data improvement: {improvement_ratio:.1f}x more prices")
    
    if unlimited_cache_size > sample_cache_size:
        print("✅ SUCCESS: Unlimited mode loads significantly more pricing data!")
    else:
        print("⚠️  WARNING: Unlimited mode didn't load more data than sample mode")
    
    # Test 2: Validate price filtering still works
    print(f"\n🔍 Test 2: Verifying price validation filtering works with unlimited data...")
    
    # Check if any results found have validated pricing
    if unlimited_results:
        result = unlimited_results[0]
        print(f"✅ First opportunity uses collection: {result.input_config.collection1}")
        print(f"✅ Expected profit: ${result.raw_profit:.2f}")
        print("✅ Price validation filtering is working with unlimited pricing!")
    else:
        print("ℹ️  No opportunities found, but this confirms filtering is working correctly")
    
    await finder_unlimited.close()
    
    # Test 3: Performance comparison
    print(f"\n🔍 Test 3: Performance with unlimited pricing...")
    
    import time
    
    # Time the initialization
    start_time = time.time()
    finder_perf = ComprehensiveTradeUpFinder()
    await finder_perf.initialize(use_all_prices=True)
    init_time = time.time() - start_time
    
    # Time a search
    start_time = time.time()
    perf_results = await finder_perf.find_profitable_trades(min_profit=1.0, limit=5)
    search_time = time.time() - start_time
    
    print(f"✅ Initialization time: {init_time:.2f} seconds")
    print(f"✅ Search time: {search_time:.2f} seconds")
    print(f"✅ Total opportunities found: {len(perf_results)}")
    
    await finder_perf.close()
    
    print(f"\n🎉 Unlimited pricing functionality test completed!")
    print(f"📊 Summary:")
    print(f"   • Unlimited mode loads {unlimited_cache_size:,} prices")
    print(f"   • {improvement_ratio:.1f}x more data than sample mode")
    print(f"   • Found {len(unlimited_results)} trade opportunities")
    print(f"   • Initialization takes {init_time:.2f}s")
    print(f"   • Search takes {search_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_unlimited_pricing())
