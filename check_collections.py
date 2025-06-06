#!/usr/bin/env python3
"""
Check collections in the comprehensive database
"""

import sqlite3

def check_collections():
    conn = sqlite3.connect('data/comprehensive_skins.db')
    cursor = conn.cursor()
    
    print("🔍 Checking collections in comprehensive database...")
    
    # Check all collections
    cursor.execute('''
        SELECT DISTINCT collection, COUNT(*) as count
        FROM comprehensive_skins 
        WHERE collection IS NOT NULL 
        GROUP BY collection 
        ORDER BY count DESC 
        LIMIT 20
    ''')
    
    results = cursor.fetchall()
    print(f"\n📊 Found {len(results)} unique collections:")
    
    for collection, count in results:
        print(f"  {collection}: {count} skins")
    
    # Check for Unknown collections
    cursor.execute("SELECT COUNT(*) FROM comprehensive_skins WHERE collection = 'Unknown' OR collection IS NULL")
    unknown_count = cursor.fetchone()[0]
    print(f"\n❓ Unknown/NULL collections: {unknown_count}")
    
    # Sample skins with collections
    cursor.execute('''
        SELECT market_hash_name, collection, rarity 
        FROM comprehensive_skins 
        WHERE collection IS NOT NULL AND collection != 'Unknown'
        LIMIT 5
    ''')
    
    print(f"\n🎯 Sample skins with collections:")
    for name, collection, rarity in cursor.fetchall():
        print(f"  {name} -> {collection} ({rarity})")
    
    conn.close()

if __name__ == "__main__":
    check_collections()
