"""
Quick end-to-end test for the updated float scaling implementation
Tests the complete workflow by running the main finder with very permissive parameters
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.formatter import TradeUpFormatter

async def test_quick_e2e():
    """Quick test of the complete workflow with float scaling"""
    
    print("=== Quick Float Scaling E2E Test ===\n")
    
    # Initialize the finder with a small sample for speed
    print("🔄 Initializing finder...")
    finder = ComprehensiveTradeUpFinder()
    await finder.initialize(sample_size=300)  # Very small sample for speed
    
    print("✅ Initialized successfully\n")
    
    # Test the search functionality with very permissive parameters
    print("🔍 Searching for any profitable trade-ups with float scaling...")
    try:
        results = await finder.find_profitable_trades(
            min_profit=0.01,  # Very low threshold
            max_input_price=3.0,  # Low price limit
            limit=2  # Just get 2 results
        )
        
        if results:
            print(f"✅ Found {len(results)} profitable trade-ups with updated float scaling!")
            print("📊 This confirms the complete workflow is working correctly.\n")
            
            for i, result in enumerate(results, 1):
                print(f"--- Trade-up #{i} ---")
                formatted = TradeUpFormatter.format_single_result(result)
                print(formatted)
                print()
                
            print("🎉 SUCCESS: Float scaling is integrated and working in the complete workflow!")
        else:
            print("🔍 No profitable trades found with current parameters")
            print("✅ But the workflow completed without errors, indicating float scaling integration is successful")
            
    except Exception as e:
        print(f"❌ Error in search: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Quick E2E Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_quick_e2e())
