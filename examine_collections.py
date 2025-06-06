#!/usr/bin/env python3
"""
Examine collection data in the database
"""

import sqlite3
import json

def main():
    conn = sqlite3.connect('data/comprehensive_skins.db')
    cursor = conn.cursor()
    cursor.execute('SELECT raw_data FROM comprehensive_skins LIMIT 5')
    rows = cursor.fetchall()
    
    print('=== COLLECTION DATA EXAMPLES ===')
    for i, row in enumerate(rows):
        if row[0]:
            data = json.loads(row[0])
            print(f'\nSkin {i+1}: {data["market_hash_name"]}')
            if 'collections' in data:
                collections = data['collections']
                if collections:
                    for collection in collections:
                        print(f'  Collection: {collection.get("name", "Unknown")}')
                else:
                    print('  Collections: Empty list')
            else:
                print('  No collections field')
    
    conn.close()

if __name__ == "__main__":
    main()
