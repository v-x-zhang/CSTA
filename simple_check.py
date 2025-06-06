#!/usr/bin/env python3
import sqlite3
import json

try:
    conn = sqlite3.connect('data/comprehensive_skins.db')
    cursor = conn.cursor()
    cursor.execute('SELECT raw_data FROM comprehensive_skins WHERE raw_data IS NOT NULL LIMIT 1')
    row = cursor.fetchone()

    if row and row[0]:
        data = json.loads(row[0])
        with open('collection_check.txt', 'w') as f:
            f.write(f"Sample API response keys: {list(data.keys())}\n")
            if 'collections' in data:
                f.write(f"Collections field: {data['collections']}\n")
            f.write(f"Market name: {data.get('market_hash_name', 'N/A')}\n")
        print("Output written to collection_check.txt")
    else:
        print("No raw data found")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
