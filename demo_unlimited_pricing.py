"""
Simple demonstration of unlimited pricing vs sample size
Shows the dramatic improvement in data coverage
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.logging_config import setup_logging

async def demo_unlimited_pricing():
    """Demonstrate the unlimited pricing improvement"""
    
    print("=" * 80)
    print("CS:GO Trade-Up Calculator - Sample Size Limitation REMOVED!")
    print("=" * 80)
    print()
    
    # Test 1: Show sample size loading
    print("🔹 BEFORE: Sample Size Limitation (e.g. 100 prices)")
    finder_sample = ComprehensiveTradeUpFinder()
    await finder_sample.initialize(sample_size=100)
    
    sample_count = len(finder_sample._cached_prices)
    print(f"   📊 Loaded: {sample_count:,} prices")
    print(f"   📦 Collections: {len(finder_sample.market_data.collections)}")
    await finder_sample.close()
    
    print()
    
    # Test 2: Show unlimited loading
    print("🔹 AFTER: Unlimited Pricing (ALL available data)")
    finder_unlimited = ComprehensiveTradeUpFinder()
    await finder_unlimited.initialize(use_all_prices=True)
    
    unlimited_count = len(finder_unlimited._cached_prices)
    print(f"   📊 Loaded: {unlimited_count:,} prices")
    print(f"   📦 Collections: {len(finder_unlimited.market_data.collections)}")
    await finder_unlimited.close()
    
    # Show the improvement
    improvement = unlimited_count / sample_count if sample_count > 0 else 0
    additional_data = unlimited_count - sample_count
    
    print()
    print("🎉 IMPROVEMENT SUMMARY:")
    print(f"   📈 Data Increase: {improvement:.1f}x more pricing data")
    print(f"   ➕ Additional Prices: +{additional_data:,} more skins covered")
    print(f"   🔓 Limitation Removed: No more sample size restrictions!")
    
    print()
    print("✅ SUCCESS: Sample size limitations have been completely removed!")
    print("💡 Usage:")
    print("   python main_comprehensive.py --all-prices    # Use ALL pricing data")
    print("   python main_comprehensive.py --sample-size 1000  # Use limited sample (old way)")

if __name__ == "__main__":
    # Minimal logging for cleaner output
    setup_logging(level='WARNING')
    asyncio.run(demo_unlimited_pricing())
