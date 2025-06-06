"""
Main entry point for the CS2 Trade-up Calculator.
Provides both CLI interface and example usage.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.logging_config import setup_logging
from src.trade_up_finder import TradeUpFinder
from src.formatter import TradeUpFormatter

async def main():
    """Main application entry point"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='CS2 Trade-up Calculator')
    parser.add_argument('--min-profit', type=float, default=1.0,
                       help='Minimum profit threshold in dollars (default: 1.0)')
    parser.add_argument('--max-price', type=float, default=None,
                       help='Maximum input skin price in dollars')
    parser.add_argument('--collections', nargs='+', default=None,
                       help='Target collections to focus on')
    parser.add_argument('--guaranteed-only', action='store_true',
                       help='Show only guaranteed profit trades')
    parser.add_argument('--limit', type=int, default=10,
                       help='Maximum number of results (default: 10)')    
    parser.add_argument('--refresh', action='store_true',
                       help='Force refresh of market data')
    parser.add_argument('--summary', action='store_true',
                       help='Show market data summary')
    parser.add_argument('--table', action='store_true',
                       help='Show results in table format')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    parser.add_argument('--use-mock-data', action='store_true',
                       help='Use mock data for testing instead of live APIs')
    parser.add_argument('--use-profitable-mock', action='store_true',
                       help='Use profitable mock data scenarios for demonstration')
    parser.add_argument('--limit-items', type=int, default=None,
                       help='Limit number of items fetched from API (for testing)')
    parser.add_argument('--use-csfloat', action='store_true',
                       help='Enable CSFloat API for float data (may cause rate limiting)')
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    try:
        # Initialize the trade-up finder
        print("🔄 Initializing CS2 Trade-up Calculator...")
        
        # If using profitable mock, enable mock data
        use_mock = args.use_mock_data or args.use_profitable_mock
        finder = TradeUpFinder(
            use_mock_data=use_mock, 
            use_profitable_mock=args.use_profitable_mock,
            limit_items=args.limit_items,
            use_csfloat=args.use_csfloat
        )
        
        await finder.initialize(force_refresh=args.refresh)
        
        # Show market summary if requested
        if args.summary:
            summary = finder.get_market_summary()
            print("\n" + TradeUpFormatter.format_market_summary(summary))
            print()
        
        # Find trade-up opportunities
        if args.guaranteed_only:
            print("🔍 Searching for guaranteed profit trade-ups...")
            results = await finder.find_guaranteed_profit_trades(
                max_input_price=args.max_price,
                target_collections=args.collections,
                limit=args.limit
            )
        else:
            print(f"🔍 Searching for profitable trade-ups (min profit: ${args.min_profit})...")
            results = await finder.find_profitable_trades(
                min_profit=args.min_profit,
                max_input_price=args.max_price,
                target_collections=args.collections,
                limit=args.limit
            )
        
        # Display results
        if not results:
            print("❌ No profitable trade-up opportunities found with the specified criteria.")
            print("\nTry adjusting your parameters:")
            print("  - Lower the minimum profit requirement")
            print("  - Increase the maximum input price")
            print("  - Use --refresh to get latest market data")
        else:
            print(f"\n✅ Found {len(results)} profitable trade-up opportunities!\n")
            
            if args.table:
                print(TradeUpFormatter.format_summary_table(results))
            else:
                title = "GUARANTEED PROFIT TRADES" if args.guaranteed_only else "PROFITABLE TRADES"
                print(TradeUpFormatter.format_multiple_results(results, title))
        
        await finder.close()
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

async def example_usage():
    """Example usage of the trade-up finder"""
    print("🔄 Example: Finding best trade-up opportunities...")
    
    # Setup logging
    setup_logging(level='INFO')
    
    # Create finder
    finder = TradeUpFinder()
    await finder.initialize()
    
    # Find profitable trades
    results = await finder.find_profitable_trades(
        min_profit=2.0,  # At least $2 profit
        max_input_price=10.0,  # Max $10 per input skin
        limit=5
    )
    
    if results:
        print(f"\n✅ Found {len(results)} opportunities:")
        print(TradeUpFormatter.format_summary_table(results))
        
        # Show detailed view of best opportunity
        print("\n" + "="*80)
        print("BEST OPPORTUNITY DETAILS:")
        print("="*80)
        print(TradeUpFormatter.format_single_result(results[0]))
    else:
        print("❌ No profitable opportunities found")
    
    await finder.close()

if __name__ == "__main__":
    # Run the main CLI application
    asyncio.run(main())
