#!/usr/bin/env python3
"""
Comprehensive CS2 Skin Database Builder
Uses PriceEmpire's paid items endpoint to build a complete local database
of all CS2 skins with accurate collection, rarity, and pricing data.
"""

import asyncio
import aiohttp
import sqlite3
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.logging_config import setup_logging
import logging

class ComprehensiveDatabaseBuilder:
    """Builds comprehensive CS2 skin database from PriceEmpire API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        self.db_path = Path("data/comprehensive_skins.db")
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        # PriceEmpire API endpoints
        self.items_endpoint = "https://api.pricempire.com/v4/paid/items"
        
        # Weapon categories for filtering
        self.weapon_categories = {
            'rifles': ['AK-47', 'M4A4', 'M4A1-S', 'AWP', 'SSG 08', 'SCAR-20', 'G3SG1', 'Galil AR', 'FAMAS', 'AUG', 'SG 553'],
            'pistols': ['Glock-18', 'USP-S', 'P2000', 'P250', 'Five-SeveN', 'Tec-9', 'CZ75-Auto', 'Desert Eagle', 'Dual Berettas', 'R8 Revolver'],
            'smgs': ['MAC-10', 'MP9', 'MP7', 'UMP-45', 'P90', 'PP-Bizon', 'MP5-SD'],
            'shotguns': ['Nova', 'XM1014', 'Sawed-Off', 'MAG-7'],
            'lmgs': ['M249', 'Negev']
        }
        
        # Float condition mappings
        self.float_conditions = {
            'Factory New': (0.0, 0.07),
            'Minimal Wear': (0.07, 0.15), 
            'Field-Tested': (0.15, 0.38),
            'Well-Worn': (0.38, 0.45),
            'Battle-Scarred': (0.45, 1.0)
        }
        
        # Rarity hierarchy 
        self.rarity_hierarchy = [
            'Consumer Grade',
            'Industrial Grade', 
            'Mil-Spec Grade',
            'Restricted',
            'Classified',
            'Covert',
            'Contraband'
        ]

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'CS2-TradeUp-Calculator/1.0',
                'Accept': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def init_database(self):
        """Initialize the comprehensive skins database"""
        self.logger.info("Initializing comprehensive skins database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS comprehensive_skins")
        cursor.execute("DROP TABLE IF EXISTS collections")
        cursor.execute("DROP TABLE IF EXISTS weapon_categories")
        cursor.execute("DROP TABLE IF EXISTS metadata")
        
        # Create comprehensive skins table
        cursor.execute("""
            CREATE TABLE comprehensive_skins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_hash_name TEXT UNIQUE NOT NULL,
                weapon_name TEXT NOT NULL,
                skin_name TEXT NOT NULL,
                condition_name TEXT,
                rarity TEXT,
                collection TEXT,
                weapon_category TEXT,
                stattrak BOOLEAN DEFAULT FALSE,
                souvenir BOOLEAN DEFAULT FALSE,
                min_float REAL,
                max_float REAL,
                current_price REAL,
                price_7d_avg REAL,
                price_30d_avg REAL,
                volume_7d INTEGER,
                volume_30d INTEGER,
                liquidity_score INTEGER,
                last_updated TIMESTAMP,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create collections table
        cursor.execute("""
            CREATE TABLE collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_name TEXT UNIQUE NOT NULL,
                collection_type TEXT,
                release_date TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create weapon categories table
        cursor.execute("""
            CREATE TABLE weapon_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                weapon_name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create metadata table
        cursor.execute("""
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX idx_market_hash_name ON comprehensive_skins(market_hash_name)")
        cursor.execute("CREATE INDEX idx_weapon_name ON comprehensive_skins(weapon_name)")
        cursor.execute("CREATE INDEX idx_collection ON comprehensive_skins(collection)")
        cursor.execute("CREATE INDEX idx_rarity ON comprehensive_skins(rarity)")
        cursor.execute("CREATE INDEX idx_weapon_category ON comprehensive_skins(weapon_category)")
        cursor.execute("CREATE INDEX idx_condition ON comprehensive_skins(condition_name)")
        
        conn.commit()
        conn.close()
        
        self.logger.info("Database initialized successfully")

    def parse_skin_name(self, market_hash_name: str) -> Dict[str, str]:
        """
        Parse market hash name to extract weapon, skin, condition, etc.
        
        Examples:
        - "AK-47 | Redline (Field-Tested)" -> weapon="AK-47", skin="Redline", condition="Field-Tested"
        - "StatTrak™ M4A4 | Howl (Factory New)" -> weapon="M4A4", skin="Howl", condition="Factory New", stattrak=True
        - "Souvenir AWP | Dragon Lore (Factory New)" -> weapon="AWP", skin="Dragon Lore", condition="Factory New", souvenir=True
        """
        result = {
            'weapon_name': '',
            'skin_name': '',
            'condition_name': '',
            'stattrak': False,
            'souvenir': False
        }
        
        name = market_hash_name
        
        # Check for StatTrak™
        if name.startswith('StatTrak™ '):
            result['stattrak'] = True
            name = name[10:]  # Remove "StatTrak™ "
            
        # Check for Souvenir
        if name.startswith('Souvenir '):
            result['souvenir'] = True
            name = name[9:]  # Remove "Souvenir "
        
        # Extract condition (in parentheses at the end)
        condition_match = re.search(r'\(([^)]+)\)$', name)
        if condition_match:
            result['condition_name'] = condition_match.group(1)
            name = name[:condition_match.start()].strip()
        
        # Split weapon and skin by " | "
        if ' | ' in name:
            weapon, skin = name.split(' | ', 1)
            result['weapon_name'] = weapon.strip()
            result['skin_name'] = skin.strip()
        else:
            # Handle items without skin names (vanilla weapons, etc.)
            result['weapon_name'] = name.strip()
            result['skin_name'] = ''
        
        return result

    def get_weapon_category(self, weapon_name: str) -> str:
        """Determine weapon category from weapon name"""
        for category, weapons in self.weapon_categories.items():
            if weapon_name in weapons:
                return category
        return 'other'    
        
    def get_float_range(self, condition_name: str) -> Tuple[float, float]:
        """Get float range for a condition"""
        return self.float_conditions.get(condition_name, (0.0, 1.0))

    async def fetch_all_items(self) -> List[Dict]:
        """Fetch all items from PriceEmpire API"""
        self.logger.info("Fetching all items from PriceEmpire API...")
        
        if not self.api_key:
            self.logger.error("API key required for PriceEmpire paid endpoint")
            raise ValueError("API key required for PriceEmpire paid endpoint")
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
        
        # Add required query parameters
        params = {
            'app_id': 730,  # CS2 app ID
            'language': 'en',  # Required language parameter
            'currency': 'USD'
        }
        
        try:
            async with self.session.get(self.items_endpoint, headers=headers, params=params) as response:
                self.logger.info(f"API Response status: {response.status}")
                
                if response.status == 401:
                    self.logger.error("Authentication failed - check API key")
                    raise ValueError("Invalid API key")
                elif response.status == 403:
                    self.logger.error("Access forbidden - check API subscription")
                    raise ValueError("Access forbidden - check API subscription")
                elif response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"API request failed: {response.status} - {error_text}")
                    raise ValueError(f"API request failed: {response.status}")
                
                data = await response.json()
                
                # Handle different response formats
                if isinstance(data, dict):
                    items = data.get('items', data.get('data', []))
                else:
                    items = data
                
                self.logger.info(f"Successfully fetched {len(items)} items from API")
                return items
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error fetching items: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            raise

    def filter_cs2_skins(self, items: List[Dict]) -> List[Dict]:
        """Filter items to only include CS2 weapon skins"""
        self.logger.info("Filtering CS2 weapon skins...")
        
        cs2_skins = []
        
        for item in items:
            market_hash_name = item.get('market_hash_name', '')
            
            # Skip non-CS2 items
            if not market_hash_name:
                continue
                
            # Skip stickers, cases, keys, etc.
            skip_keywords = [
                'Sticker |', 'Case', 'Key', 'Pin', 'Patch', 'Graffiti',
                'Music Kit', 'Capsule', 'Package', 'Coupon', 'Gift'
            ]
            
            if any(keyword in market_hash_name for keyword in skip_keywords):
                continue
            
            # Parse the skin name
            parsed = self.parse_skin_name(market_hash_name)
            
            # Only include items with weapon names we recognize
            if parsed['weapon_name'] and self.get_weapon_category(parsed['weapon_name']) != 'other':
                cs2_skins.append({
                    **item,
                    **parsed
                })
        
        self.logger.info(f"Filtered to {len(cs2_skins)} CS2 weapon skins")
        return cs2_skins    
    
    def save_to_database(self, skins: List[Dict]):
        """Save processed skins to database"""
        self.logger.info("Saving skins to database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert skins
        for skin in skins:
            min_float, max_float = self.get_float_range(skin.get('condition_name', ''))
            weapon_category = self.get_weapon_category(skin['weapon_name'])
            
            # Extract rarity as string
            rarity = skin.get('rarity')
            if isinstance(rarity, dict):
                rarity = rarity.get('name', 'Unknown')
            elif not rarity:
                rarity = 'Unknown'
            
            # Extract pricing data
            current_price = None
            price_7d_avg = None
            price_30d_avg = None
            volume_7d = None
            volume_30d = None
            liquidity_score = None
            
            # Handle different price data formats
            if 'prices' in skin and skin['prices']:
                prices = skin['prices']
                if isinstance(prices, list) and prices:
                    current_price = prices[0].get('price')
                elif isinstance(prices, dict):
                    current_price = prices.get('current', prices.get('price'))
            
            # Extract additional metrics
            if 'steam_last_7d' in skin:
                price_7d_avg = skin.get('steam_last_7d')
            if 'steam_last_30d' in skin:
                price_30d_avg = skin.get('steam_last_30d')
            if 'trades_7d' in skin:
                volume_7d = skin.get('trades_7d')
            if 'trades_30d' in skin:
                volume_30d = skin.get('trades_30d')            if 'liquidity' in skin:
                liquidity_score = skin.get('liquidity')
            
            # Extract collection name from collections array
            collection_name = None
            if 'collections' in skin and skin['collections']:
                if isinstance(skin['collections'], list) and len(skin['collections']) > 0:
                    collection_name = skin['collections'][0].get('name')
            
            cursor.execute("""
                INSERT OR REPLACE INTO comprehensive_skins (
                    market_hash_name, weapon_name, skin_name, condition_name,
                    rarity, collection, weapon_category, stattrak, souvenir,
                    min_float, max_float, current_price, price_7d_avg, price_30d_avg,
                    volume_7d, volume_30d, liquidity_score, last_updated, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                skin['market_hash_name'],
                skin['weapon_name'],
                skin['skin_name'],
                skin.get('condition_name'),
                rarity,  # Use the processed string rarity
                collection_name,
                weapon_category,
                skin['stattrak'],
                skin['souvenir'],
                min_float,
                max_float,
                current_price,
                price_7d_avg,
                price_30d_avg,
                volume_7d,
                volume_30d,
                liquidity_score,
                datetime.utcnow().isoformat(),
                json.dumps(skin)
            ))
        
        # Update metadata
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ('last_full_update', datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ('total_skins', str(len(skins)), datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Successfully saved {len(skins)} skins to database")

    async def build_database(self, api_key: str):
        """Main method to build the comprehensive database"""
        self.api_key = api_key
        
        self.logger.info("Starting comprehensive database build...")
        
        # Initialize database
        self.init_database()
        
        # Fetch all items
        all_items = await self.fetch_all_items()
        
        # Filter to CS2 skins
        cs2_skins = self.filter_cs2_skins(all_items)
        
        # Save to database
        self.save_to_database(cs2_skins)
        
        self.logger.info("Comprehensive database build completed successfully!")
        
        # Print summary
        await self.print_database_summary()

    async def print_database_summary(self):
        """Print summary of database contents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total skins
        cursor.execute("SELECT COUNT(*) FROM comprehensive_skins")
        total_skins = cursor.fetchone()[0]
        
        # Skins by category
        cursor.execute("""
            SELECT weapon_category, COUNT(*) 
            FROM comprehensive_skins 
            GROUP BY weapon_category 
            ORDER BY COUNT(*) DESC
        """)
        by_category = cursor.fetchall()
        
        # Skins by rarity
        cursor.execute("""
            SELECT rarity, COUNT(*) 
            FROM comprehensive_skins 
            WHERE rarity IS NOT NULL
            GROUP BY rarity 
            ORDER BY COUNT(*) DESC
        """)
        by_rarity = cursor.fetchall()
        
        # Unique collections
        cursor.execute("""
            SELECT COUNT(DISTINCT collection) 
            FROM comprehensive_skins 
            WHERE collection IS NOT NULL
        """)
        total_collections = cursor.fetchone()[0]
        
        # Unique weapons
        cursor.execute("SELECT COUNT(DISTINCT weapon_name) FROM comprehensive_skins")
        total_weapons = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "="*60)
        print("           COMPREHENSIVE DATABASE SUMMARY")
        print("="*60)
        print(f"Total Skins: {total_skins:,}")
        print(f"Unique Weapons: {total_weapons}")
        print(f"Unique Collections: {total_collections}")
        
        print(f"\nSkins by Category:")
        for category, count in by_category:
            print(f"  {category}: {count:,}")
        
        print(f"\nSkins by Rarity:")
        for rarity, count in by_rarity:
            print(f"  {rarity or 'Unknown'}: {count:,}")
        
        print("="*60)


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build comprehensive CS2 skin database')
    parser.add_argument('--api-key', required=True, help='PriceEmpire API key')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    async with ComprehensiveDatabaseBuilder() as builder:
        await builder.build_database(args.api_key)


if __name__ == "__main__":
    asyncio.run(main())
