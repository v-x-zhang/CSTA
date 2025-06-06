"""
Main entry point for the CS2 Trade-up Calculator - Comprehensive Version
Uses comprehensive database for skin metadata + runtime pricing
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.logging_config import setup_logging
from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.formatter import TradeUpFormatter

async def main():
    """Main application entry point"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='CS2 Trade-up Calculator - Comprehensive Version')    
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
    parser.add_argument('--stop-after-one', action='store_true',
                       help='Stop after finding just one profitable trade-up')        
    parser.add_argument('--sample-size', type=int, default=2000,
                       help='Number of prices to fetch for initialization (default: 2000)')
    parser.add_argument('--not-all-prices', action='store_true',
                       help='Use ALL available pricing data instead of sample size limit')
    parser.add_argument('--use-steam-pricing', action='store_true',
                       help='Use Steam Market pricing database instead of external API')
    parser.add_argument('--summary', action='store_true',
                       help='Show market data summary')
    parser.add_argument('--table', action='store_true',
                       help='Show results in table format')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    try:        # Initialize the comprehensive trade-up finder
        print("🔄 Initializing CS2 Trade-up Calculator (Comprehensive Version)...")
        
        if args.use_steam_pricing:
            print(f"📊 Using Steam Market pricing database")
            finder = ComprehensiveTradeUpFinder(use_steam_pricing=True)
        else:
            print(f"📊 Using comprehensive database with external API pricing")
            finder = ComprehensiveTradeUpFinder(use_steam_pricing=False)
        
        if args.not_all_prices:
            print(f"💰 Fetching sample prices (limit: {args.sample_size})...")
            await finder.initialize(sample_size=args.sample_size)
        else:
            print("💰 Loading ALL available pricing data...")
            await finder.initialize(use_all_prices=True)

          # Show market summary if requested
        if args.summary:
            summary = finder.get_market_summary()
            pricing_info = finder.get_pricing_source_info()
            
            print("\\n" + "="*60)
            print("DATABASE SUMMARY")
            print("="*60)
            print(f"Total Skins: {summary.get('total_skins', 0):,}")
            print(f"Unique Weapons: {summary.get('unique_weapons', 0):,}")
            print(f"Unique Collections: {summary.get('unique_collections', 0):,}")
            print(f"Cached Prices: {summary.get('cached_prices', 0):,}")
            
            print(f"\\nPricing Source: {pricing_info.get('source', 'Unknown')}")
            print(f"Pricing Type: {pricing_info.get('type', 'Unknown')}")
            if 'total_prices' in pricing_info:
                print(f"Total Prices in DB: {pricing_info['total_prices']:,}")
            if 'average_price' in pricing_info:
                print(f"Average Price: ${pricing_info['average_price']:.2f}")
            print(f"Description: {pricing_info.get('description', 'N/A')}")
            
            if 'by_rarity' in summary:
                print("\\nSkins by Rarity:")
                for rarity, count in summary['by_rarity'].items():
                    print(f"  {rarity}: {count:,}")
            
            if 'by_category' in summary:
                print("\\nSkins by Category:")
                for category, count in summary['by_category'].items():
                    print(f"  {category}: {count:,}")
            print("="*60)
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
            # Use limit of 1 if stop-after-one is specified
            if args.stop_after_one:
                offset = 0
                while True:
                    results = await finder.find_profitable_trades(
                        min_profit=args.min_profit,
                        max_input_price=args.max_price,
                        target_collections=args.collections,
                        limit=1,
                        offset=offset
                    )

                    if not results:
                        print("❌ No more profitable trade-up opportunities found.")
                        break

                    print("\n✅ Found a profitable trade-up opportunity:\n")
                    print(TradeUpFormatter.format_single_result(results[0]))

                    user_input = input("\nWould you like to see the next trade-up? (yes/no): ").strip().lower()
                    if user_input not in ['yes', 'y']:
                        print("🛑 Stopping the search as requested.")
                        break

                    offset += 1
            else:
                results = await finder.find_profitable_trades(
                    min_profit=args.min_profit,
                    max_input_price=args.max_price,
                    target_collections=args.collections,
                    limit=args.limit
                )
    except FileNotFoundError as e:
        if 'steam_pricing.db' in str(e):
            print(f"\n❌ Steam pricing database not found!")
            print("💡 To use Steam pricing, first build the database:")
            print("   python build_steam_pricing_database.py")
            print("💡 Or run without --use-steam-pricing to use external API pricing")
        else:
            print(f"\n❌ Database Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# For standalone execution
if __name__ == "__main__":
    asyncio.run(main())

