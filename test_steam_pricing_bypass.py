"""
Test script to verify that Steam pricing bypasses validation correctly
"""

import asyncio
import logging
from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

# Configure logging to see the validation process
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_steam_pricing_bypass():
    """Test that Steam pricing bypasses validation"""
    print("🔄 Testing Steam pricing validation bypass...")
    
    # Test with Steam pricing enabled (should bypass validation)
    print("\n1. Testing with Steam pricing (should bypass validation):")
    steam_finder = ComprehensiveTradeUpFinder(use_steam_pricing=True)
    await steam_finder.initialize(sample_size=50)  # Small sample for quick test
    
    # Test with external pricing (should use validation)
    print("\n2. Testing with external pricing (should use validation):")
    external_finder = ComprehensiveTradeUpFinder(use_steam_pricing=False)
    await external_finder.initialize(sample_size=50)  # Small sample for quick test
    
    print("\n✅ Test completed!")
    print("Check the debug logs above to verify:")
    print("- Steam pricing shows: 'Using Steam pricing directly for X items (no validation needed)'")
    print("- External pricing shows: 'Price validation complete: X/Y prices validated'")

if __name__ == "__main__":
    asyncio.run(test_steam_pricing_bypass())
