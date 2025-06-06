#!/usr/bin/env python3
"""
Check pricing data in the database
"""

import sqlite3

def main():
    conn = sqlite3.connect('data/comprehensive_skins.db')
    cursor = conn.cursor()

    print('=== PRICING DATA ANALYSIS ===')
    
    # Total skins with prices
    cursor.execute('SELECT COUNT(*) FROM comprehensive_skins WHERE current_price IS NOT NULL')
    with_prices = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM comprehensive_skins')
    total = cursor.fetchone()[0]
    
    print(f'Skins with prices: {with_prices:,} / {total:,} ({with_prices/total*100:.1f}%)')
    
    # Price ranges
    cursor.execute('SELECT MIN(current_price), MAX(current_price), AVG(current_price) FROM comprehensive_skins WHERE current_price IS NOT NULL')
    result = cursor.fetchone()
    if result[0]:
        print(f'Price range: ${result[0]:.2f} - ${result[1]:.2f} (avg: ${result[2]:.2f})')
    
    # AK-47 pricing specifically
    print('\n=== AK-47 PRICING ===')
    cursor.execute('SELECT COUNT(*) FROM comprehensive_skins WHERE weapon_name = "AK-47" AND current_price IS NOT NULL')
    ak_with_prices = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM comprehensive_skins WHERE weapon_name = "AK-47"')
    ak_total = cursor.fetchone()[0]
    
    print(f'AK-47 skins with prices: {ak_with_prices} / {ak_total} ({ak_with_prices/ak_total*100:.1f}%)')
    
    # Sample AK-47 entries to see the data structure
    print('\n=== SAMPLE AK-47 DATABASE ENTRIES ===')
    cursor.execute('''
        SELECT market_hash_name, rarity, current_price, last_updated 
        FROM comprehensive_skins 
        WHERE weapon_name = "AK-47" 
        LIMIT 10
    ''')
    
    for name, rarity, price, updated in cursor.fetchall():
        price_str = f"${price:.2f}" if price else "No price"
        updated_str = updated if updated else "Never"
        print(f'  {name} ({rarity}): {price_str} | Updated: {updated_str}')
    
    # Check if we have any prices at all
    print('\n=== ANY SKINS WITH PRICES ===')
    cursor.execute('SELECT market_hash_name, current_price FROM comprehensive_skins WHERE current_price IS NOT NULL LIMIT 5')
    results = cursor.fetchall()
    if results:
        for name, price in results:
            print(f'  {name}: ${price:.2f}')
    else:
        print('  No skins have pricing data!')

    conn.close()

if __name__ == "__main__":
    main()
