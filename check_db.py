#!/usr/bin/env python3
"""
Quick database verification script
"""

import sqlite3
import json

def main():
    print("🔍 Checking Comprehensive CS2 Skin Database")
    print("=" * 50)
    
    conn = sqlite3.connect('data/comprehensive_skins.db')
    cursor = conn.cursor()
    
    # Basic stats
    cursor.execute('SELECT COUNT(*) FROM comprehensive_skins')
    total_skins = cursor.fetchone()[0]
    print(f"📊 Total skins: {total_skins:,}")
    
    # Rarity distribution
    print("\n🎯 Rarity Distribution:")
    cursor.execute('SELECT rarity, COUNT(*) FROM comprehensive_skins GROUP BY rarity ORDER BY COUNT(*) DESC')
    for rarity, count in cursor.fetchall():
        print(f"  {rarity}: {count:,}")
    
    # Top weapons
    print("\n🔫 Top 10 Weapons by Skin Count:")
    cursor.execute('SELECT weapon_name, COUNT(*) FROM comprehensive_skins GROUP BY weapon_name ORDER BY COUNT(*) DESC LIMIT 10')
    for weapon, count in cursor.fetchall():
        print(f"  {weapon}: {count:,}")
    
    # Sample high-value skins
    print("\n💎 Sample AK-47 Covert Skins:")
    cursor.execute('''
        SELECT market_hash_name, current_price 
        FROM comprehensive_skins 
        WHERE weapon_name = "AK-47" AND rarity = "Covert" 
        ORDER BY current_price DESC NULLS LAST 
        LIMIT 5
    ''')
    for name, price in cursor.fetchall():
        if price:
            print(f"  {name}: ${price:.2f}")
        else:
            print(f"  {name}: Price TBD")
    
    # Sample for trade-up calculations
    print("\n🔄 Sample Trade-Up Eligible Skins (Mil-Spec AK-47):")
    cursor.execute('''
        SELECT market_hash_name, current_price 
        FROM comprehensive_skins 
        WHERE weapon_name = "AK-47" AND rarity = "Mil-Spec Grade" 
        AND current_price IS NOT NULL
        ORDER BY current_price ASC
        LIMIT 5
    ''')
    for name, price in cursor.fetchall():
        print(f"  {name}: ${price:.2f}")
    
    conn.close()
    print("\n✅ Database verification complete!")

if __name__ == "__main__":
    main()