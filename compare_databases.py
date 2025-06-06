import sqlite3
import sys
from pathlib import Path
sys.path.append('src')

from src.runtime_pricing import RuntimePricingClient
import asyncio

async def compare_databases():
    print("🔍 Comparing database sizes...")
    
    # Check comprehensive database
    conn = sqlite3.connect('data/comprehensive_skins.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM comprehensive_skins")
    db_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT market_hash_name) FROM comprehensive_skins") 
    unique_names = cursor.fetchone()[0]
    
    cursor.execute("SELECT market_hash_name FROM comprehensive_skins LIMIT 10")
    sample_names = cursor.fetchall()
    
    print(f"📊 Comprehensive Database:")
    print(f"   Total records: {db_count:,}")
    print(f"   Unique skin names: {unique_names:,}")
    print(f"   Sample names: {[name[0] for name in sample_names[:5]]}")
    
    # Check external pricing API
    pricing = RuntimePricingClient()
    all_prices = await pricing.get_all_prices()
    
    print(f"\n💰 External Pricing API:")
    print(f"   Total items: {len(all_prices):,}")
    print(f"   Sample names: {list(all_prices.keys())[:5]}")
    
    # Check overlap
    db_names = set()
    cursor.execute("SELECT DISTINCT market_hash_name FROM comprehensive_skins")
    db_names = {row[0] for row in cursor.fetchall()}
    
    api_names = set(all_prices.keys())
    overlap = db_names.intersection(api_names)
    
    print(f"\n🔄 Overlap Analysis:")
    print(f"   Database names: {len(db_names):,}")
    print(f"   API names: {len(api_names):,}")
    print(f"   Overlap: {len(overlap):,} ({len(overlap)/len(db_names)*100:.1f}% of database)")
    
    # Check database breakdown by type
    cursor.execute("""
        SELECT 
            CASE 
                WHEN market_hash_name LIKE '%StatTrak%' THEN 'StatTrak'
                WHEN market_hash_name LIKE '%Souvenir%' THEN 'Souvenir' 
                WHEN market_hash_name LIKE '%★%' THEN 'Knife/Glove'
                ELSE 'Regular'
            END as type,
            COUNT(*) as count
        FROM comprehensive_skins 
        GROUP BY type
        ORDER BY count DESC
    """)
    breakdown = cursor.fetchall()
    
    print(f"\n📋 Database Breakdown:")
    for skin_type, count in breakdown:
        print(f"   {skin_type}: {count:,}")
    
    # Check what external API has that we don't
    missing_from_db = api_names - db_names
    missing_from_api = db_names - api_names
    
    print(f"\n❌ Missing Analysis:")
    print(f"   Items in API but not in DB: {len(missing_from_db):,}")
    print(f"   Items in DB but not in API: {len(missing_from_api):,}")
    
    if missing_from_db:
        print(f"   Sample missing from DB: {list(missing_from_db)[:5]}")
    
    if missing_from_api:
        print(f"   Sample missing from API: {list(missing_from_api)[:5]}")
      # Check schema and available columns
    cursor.execute("PRAGMA table_info(comprehensive_skins)")
    columns = cursor.fetchall()
    
    print(f"\n📋 Database Schema:")
    for col in columns:
        print(f"   {col[1]} ({col[2]})")
    
    # Check if we have collection info
    cursor.execute("SELECT market_hash_name FROM comprehensive_skins WHERE market_hash_name LIKE '%Collection%' LIMIT 5")
    collection_samples = cursor.fetchall()
    
    if collection_samples:
        print(f"\n📦 Collection samples: {[row[0] for row in collection_samples]}")
    
    # Check weapon types
    cursor.execute("""
        SELECT 
            CASE 
                WHEN market_hash_name LIKE 'AK-47%' THEN 'AK-47'
                WHEN market_hash_name LIKE 'M4A4%' THEN 'M4A4'
                WHEN market_hash_name LIKE 'AWP%' THEN 'AWP'
                WHEN market_hash_name LIKE 'Glock-18%' THEN 'Glock-18'
                WHEN market_hash_name LIKE '★%' THEN 'Knife/Glove'
                ELSE 'Other'
            END as weapon_type,
            COUNT(*) as count
        FROM comprehensive_skins 
        GROUP BY weapon_type
        ORDER BY count DESC
        LIMIT 10
    """)
    weapon_breakdown = cursor.fetchall()
    
    print(f"\n🔫 Top Weapon Types:")
    for weapon, count in weapon_breakdown:
        print(f"   {weapon}: {count:,}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(compare_databases())
