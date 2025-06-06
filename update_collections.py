#!/usr/bin/env python3
"""
Update existing comprehensive database with correct collection information
by re-processing the raw_data field that's already stored
"""

import sqlite3
import json
from pathlib import Path

def update_collections():
    """Update collection information from existing raw_data"""
    
    db_path = Path("data/comprehensive_skins.db")
    if not db_path.exists():
        print("Database not found!")
        return
    
    print("Updating collection information from existing raw data...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all records with raw_data
    cursor.execute("SELECT market_hash_name, raw_data FROM comprehensive_skins WHERE raw_data IS NOT NULL")
    records = cursor.fetchall()
    
    print(f"Processing {len(records)} records...")
    
    updated_count = 0
    collection_counts = {}
    
    for market_hash_name, raw_data_str in records:
        try:
            raw_data = json.loads(raw_data_str)
            
            # Extract collection name
            collection_name = None
            if 'collections' in raw_data and raw_data['collections']:
                if isinstance(raw_data['collections'], list) and len(raw_data['collections']) > 0:
                    collection_name = raw_data['collections'][0].get('name')
            
            if collection_name:
                # Update the collection field
                cursor.execute(
                    "UPDATE comprehensive_skins SET collection = ? WHERE market_hash_name = ?",
                    (collection_name, market_hash_name)
                )
                updated_count += 1
                collection_counts[collection_name] = collection_counts.get(collection_name, 0) + 1
        
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error processing {market_hash_name}: {e}")
            continue
    
    # Commit changes
    conn.commit()
    
    print(f"Updated {updated_count} records with collection information")
    print(f"Found {len(collection_counts)} unique collections:")
    
    # Show top collections
    sorted_collections = sorted(collection_counts.items(), key=lambda x: x[1], reverse=True)
    for collection, count in sorted_collections[:15]:
        print(f"   {collection}: {count} skins")
    
    if len(sorted_collections) > 15:
        print(f"   ... and {len(sorted_collections) - 15} more collections")
    
    # Verify the update
    cursor.execute("SELECT COUNT(*) FROM comprehensive_skins WHERE collection IS NOT NULL AND collection != 'Unknown'")
    with_collections = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM comprehensive_skins")
    total = cursor.fetchone()[0]
    
    print(f"\nFinal stats:")
    print(f"   Skins with collections: {with_collections:,} / {total:,} ({with_collections/total*100:.1f}%)")
    
    conn.close()
    print("Collection update complete!")

if __name__ == "__main__":
    update_collections()
