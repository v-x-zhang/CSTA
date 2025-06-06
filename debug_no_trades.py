"""
Debug script to understand why no trade-ups are being found
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def debug_trade_up_finder():
    """Debug why no trade-ups are found"""
    
    print("=== Debugging Trade-up Finder ===\n")
    
    # Initialize the finder
    print("🔄 Initializing finder...")
    finder = ComprehensiveTradeUpFinder()
    await finder.initialize(sample_size=500)  # Small sample for debugging
    
    print(f"✅ Initialized with {len(finder._cached_prices)} cached prices\n")
    
    # Check collections and rarities
    print("📊 Database overview:")
    consumer_collections = finder.db_manager.get_collections_by_rarity('Consumer Grade')
    industrial_collections = finder.db_manager.get_collections_by_rarity('Industrial Grade')
    
    print(f"Collections with Consumer Grade skins: {len(consumer_collections)}")
    print(f"Collections with Industrial Grade skins: {len(industrial_collections)}")
    
    # Find collections that have both Consumer and Industrial
    valid_collections = set(consumer_collections) & set(industrial_collections)
    print(f"Collections with BOTH Consumer and Industrial: {len(valid_collections)}")
    
    if valid_collections:
        # Test a specific collection
        test_collection = list(valid_collections)[0]
        print(f"\n🧪 Testing collection: {test_collection}")
        
        # Get skins for this collection
        consumer_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Consumer Grade')
        industrial_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Industrial Grade')
        
        print(f"Consumer Grade skins: {len(consumer_skins)}")
        print(f"Industrial Grade skins: {len(industrial_skins)}")
        
        if consumer_skins and industrial_skins:
            # Check pricing data availability
            consumer_with_prices = 0
            industrial_with_prices = 0
            
            for skin in consumer_skins:
                if skin['market_hash_name'] in finder._cached_prices:
                    consumer_with_prices += 1
                    
            for skin in industrial_skins:
                if skin['market_hash_name'] in finder._cached_prices:
                    industrial_with_prices += 1
            
            print(f"Consumer skins with prices: {consumer_with_prices}/{len(consumer_skins)}")
            print(f"Industrial skins with prices: {industrial_with_prices}/{len(industrial_skins)}")
            
            # Check validation status
            consumer_valid = 0
            consumer_invalid = 0
            consumer_unvalidated = 0
            
            for skin in consumer_skins[:10]:  # Check first 10
                validation_status = finder.db_manager.get_price_validation_status(skin['market_hash_name'])
                if validation_status:
                    status = validation_status.get('status', 'unvalidated')
                    if status == 'valid':
                        consumer_valid += 1
                    elif status == 'invalid':
                        consumer_invalid += 1
                    else:
                        consumer_unvalidated += 1
                else:
                    consumer_unvalidated += 1
            
            print(f"\nPrice validation status (first 10 consumer skins):")
            print(f"Valid: {consumer_valid}, Invalid: {consumer_invalid}, Unvalidated: {consumer_unvalidated}")
            
            # Show example prices
            print(f"\n💰 Example pricing data:")
            for i, skin in enumerate(consumer_skins[:5]):
                name = skin['market_hash_name']
                price = finder._cached_prices.get(name, 'N/A')
                validation = finder.db_manager.get_price_validation_status(name)
                validation_status = validation.get('status', 'unvalidated') if validation else 'unvalidated'
                print(f"  {i+1}. {name}: ${price} (status: {validation_status})")
        
        # Try to manually calculate a trade-up
        print(f"\n🔄 Attempting to calculate trade-up for {test_collection}...")
        try:
            result = await finder._calculate_single_collection_tradeup(
                input_skins=consumer_skins,
                input_rarity='Consumer Grade',
                input_prices=[1.0] * len(consumer_skins),  # Mock prices
                output_rarity='Industrial Grade',
                collection=test_collection,
                min_profit=-10.0,  # Very permissive
                max_input_price=10.0
            )
            
            if result:
                print(f"✅ Trade-up calculation successful!")
                print(f"Expected profit: ${result.expected_profit:.2f}")
            else:
                print(f"❌ Trade-up calculation returned None")
                
        except Exception as e:
            print(f"❌ Error calculating trade-up: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    asyncio.run(debug_trade_up_finder())
