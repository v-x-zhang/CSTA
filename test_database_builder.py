#!/usr/bin/env python3
"""
Test script for the comprehensive database builder
Tests with PriceEmpire API and builds a sample database
"""

import asyncio
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from build_comprehensive_database import ComprehensiveDatabaseBuilder
from src.logging_config import setup_logging


async def test_api_access(api_key: str):
    """Test API access and show sample data"""
    print("🔍 Testing PriceEmpire API access...")
    
    async with ComprehensiveDatabaseBuilder(api_key) as builder:
        try:
            # Test API access
            items = await builder.fetch_all_items()
            
            print(f"✅ Successfully connected to API")
            print(f"📊 Total items returned: {len(items):,}")
            
            # Show sample items
            print("\n🔬 Sample items:")
            for i, item in enumerate(items[:5]):
                market_name = item.get('market_hash_name', 'Unknown')
                rarity = item.get('rarity', 'Unknown')
                collection = item.get('collection', 'Unknown')
                print(f"  {i+1}. {market_name}")
                print(f"     Rarity: {rarity}")
                print(f"     Collection: {collection}")
                print()
            
            # Filter to CS2 skins
            cs2_skins = builder.filter_cs2_skins(items)
            print(f"🎯 CS2 weapon skins: {len(cs2_skins):,}")
            
            # Show sample CS2 skins
            print("\n🔫 Sample CS2 weapon skins:")
            for i, skin in enumerate(cs2_skins[:5]):
                print(f"  {i+1}. {skin['market_hash_name']}")
                print(f"     Weapon: {skin['weapon_name']}")
                print(f"     Skin: {skin['skin_name']}")
                print(f"     Condition: {skin.get('condition_name', 'N/A')}")
                print(f"     Rarity: {skin.get('rarity', 'Unknown')}")
                print(f"     Collection: {skin.get('collection', 'Unknown')}")
                print()
            
            return True
            
        except Exception as e:
            print(f"❌ API test failed: {e}")
            return False


async def build_sample_database(api_key: str, limit: int = 1000):
    """Build a sample database with limited items"""
    print(f"🏗️ Building sample database (limit: {limit} items)...")
    
    async with ComprehensiveDatabaseBuilder(api_key) as builder:
        # Initialize database
        builder.init_database()
        
        # Fetch items
        all_items = await builder.fetch_all_items()
        
        # Limit items for testing
        limited_items = all_items[:limit]
        print(f"📦 Using {len(limited_items)} items for sample database")
        
        # Filter to CS2 skins
        cs2_skins = builder.filter_cs2_skins(limited_items)
        
        # Save to database
        builder.save_to_database(cs2_skins)
        
        # Print summary
        await builder.print_database_summary()


def load_api_key_from_config() -> str:
    """Load API key from config file"""
    config_path = Path("config/config.json")
    
    if not config_path.exists():
        return ""
    
    try:
        with open(config_path, 'r') as f:
            # Remove comments from JSON
            content = f.read()
            lines = content.split('\n')
            clean_lines = [line for line in lines if not line.strip().startswith('//')]
            clean_content = '\n'.join(clean_lines)
            
            config = json.loads(clean_content)
            return config.get('api', {}).get('pricempire_api_key', '')
    except Exception as e:
        print(f"⚠️ Could not load API key from config: {e}")
        return ""


async def main():
    """Main function"""
    setup_logging(level='INFO')
    
    print("🚀 CS2 Comprehensive Database Builder - Test")
    print("=" * 50)
    
    # Try to load API key from config
    api_key = load_api_key_from_config()
    
    if not api_key:
        print("⚠️ No API key found in config file")
        print("Please add your PriceEmpire API key to config/config.json:")
        print('  "pricempire_api_key": "your_api_key_here"')
        print("\nOr provide it as a command line argument:")
        print("  python test_database_builder.py --api-key YOUR_KEY")
        
        import sys
        if len(sys.argv) > 2 and sys.argv[1] == '--api-key':
            api_key = sys.argv[2]
        else:
            return
    
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Test API access
    if await test_api_access(api_key):
        print("\n" + "=" * 50)
        
        # Ask user if they want to build sample database
        response = input("Build sample database? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            await build_sample_database(api_key, limit=5000)
            
            print("\n🎉 Sample database built successfully!")
            print("You can now examine the data in: data/comprehensive_skins.db")
            print("\nNext steps:")
            print("1. Review the sample data quality")
            print("2. Run the full database build if satisfied")
            print("3. Update the trade-up calculator to use the new database")
        else:
            print("Sample database build skipped.")
    else:
        print("❌ Cannot proceed without working API access")


if __name__ == "__main__":
    asyncio.run(main())
