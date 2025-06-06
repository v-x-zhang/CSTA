#!/usr/bin/env python3
"""
Debug rarity values in the database
"""

import sqlite3

def main():
    conn = sqlite3.connect('data/comprehensive_skins.db')
    cursor = conn.cursor()

    print('=== RARITY VALUES IN DATABASE ===')
    cursor.execute('SELECT DISTINCT rarity FROM comprehensive_skins ORDER BY rarity')
    rarities = cursor.fetchall()
    for rarity in rarities:
        print(f'  "{rarity[0]}"')

    print('\n=== AK-47 RARITY DISTRIBUTION ===')
    cursor.execute('SELECT rarity, COUNT(*) FROM comprehensive_skins WHERE weapon_name = "AK-47" GROUP BY rarity ORDER BY COUNT(*) DESC')
    for rarity, count in cursor.fetchall():
        print(f'  {rarity}: {count}')

    print('\n=== SAMPLE AK-47 SKINS BY RARITY ===')
    for rarity_name in ['Consumer Grade', 'Industrial Grade', 'Mil-Spec Grade', 'Restricted', 'Classified', 'Covert']:
        cursor.execute('SELECT market_hash_name FROM comprehensive_skins WHERE weapon_name = "AK-47" AND rarity = ? LIMIT 3', (rarity_name,))
        skins = cursor.fetchall()
        if skins:
            print(f'{rarity_name}:')
            for skin in skins:
                print(f'  - {skin[0]}')
        else:
            print(f'{rarity_name}: No skins found')

    print('\n=== CHECKING PRICES FOR AK-47 SKINS ===')
    cursor.execute('SELECT market_hash_name, rarity, current_price FROM comprehensive_skins WHERE weapon_name = "AK-47" AND current_price IS NOT NULL ORDER BY current_price DESC LIMIT 10')
    for name, rarity, price in cursor.fetchall():
        print(f'  {name} ({rarity}): ${price:.2f}')

    conn.close()

if __name__ == "__main__":
    main()
