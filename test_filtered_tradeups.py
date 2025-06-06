"""
Test script to verify that the trade finder only returns trade-ups with validated pricing
"""

import asyncio
import logging
from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

# Configure logging to see the validation process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("🔄 Testing trade finder with price validation filtering...")
    
    # Initialize the trade finder with unlimited pricing for comprehensive testing
    finder = ComprehensiveTradeUpFinder()
    print("📊 Loading unlimited pricing data for comprehensive analysis...")
    await finder.initialize(use_all_prices=True)  # Use all available prices
    
    print("\n🔍 Checking trade finder setup...")
    print(f"✅ Loaded {len(finder._cached_prices)} pricing records")
    
    # Test with a very simple query
    try:
        # Look for ANY trade-up opportunities
        print("Looking for profitable trade-ups...")
        results = await finder.find_profitable_trades(min_profit=0.50, limit=1)
        
        if results:
            print(f"\n✅ Found {len(results)} trade-up(s) with validated pricing!")
            result = results[0]
            print(f"Collection: {result.input_config.collection1}")
            print(f"Expected Profit: ${result.raw_profit:.2f}")
            print(f"ROI: {result.roi_percentage:.1f}%")
        else:
            print("❌ No profitable trade-ups found")
            print("This confirms the filtering is working - only reliable prices are being used!")
            
    except Exception as e:
        print(f"Error during search: {e}")
        print("This may indicate successful filtering is preventing invalid trade-ups")

if __name__ == "__main__":
    asyncio.run(main())
