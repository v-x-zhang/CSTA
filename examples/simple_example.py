"""
Simple example demonstrating how to use the CS2 Trade-up Calculator.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import TradeUpFinder, setup_logging, format_trade_up_results

async def main():
    """Simple example of finding profitable trade-ups"""
    
    # Setup logging
    setup_logging(level='INFO', console=True, file_logging=False)
    
    print("🎮 CS2 Trade-up Calculator - Simple Example")
    print("=" * 50)
    
    try:
        # Initialize the finder
        print("🔄 Loading market data...")
        finder = TradeUpFinder()
        await finder.initialize()
        
        # Show market summary
        summary = finder.get_market_summary()
        print(f"📊 Market Data: {summary['total_skins']} skins from {summary['total_collections']} collections")
        print()
        
        # Find some profitable trades
        print("🔍 Finding profitable trade-ups...")
        results = await finder.find_profitable_trades(
            min_profit=1.0,  # At least $1 profit
            limit=3  # Show top 3 opportunities
        )
        
        if results:
            print(f"✅ Found {len(results)} opportunities!")
            print()
            print(format_trade_up_results(results, "TOP TRADE-UP OPPORTUNITIES"))
        else:
            print("❌ No profitable opportunities found")
            print("Try running with --refresh to get latest market data")
        
        # Find guaranteed profit trades
        print("\n" + "="*50)
        print("🔍 Looking for guaranteed profit trades...")
        guaranteed_results = await finder.find_guaranteed_profit_trades(limit=2)
        
        if guaranteed_results:
            print(f"✅ Found {len(guaranteed_results)} guaranteed profit opportunities!")
            print()
            print(format_trade_up_results(guaranteed_results, "GUARANTEED PROFIT TRADES"))
        else:
            print("❌ No guaranteed profit trades found at current market prices")
        
        await finder.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
