"""
Comprehensive Database Manager for CS2 Trade-up Calculator
Works with the comprehensive skins database built by build_comprehensive_database.py
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from pathlib import Path

try:
    from .models import Skin, MarketData, CollectionInfo
except ImportError:
    from models import Skin, MarketData, CollectionInfo

logger = logging.getLogger(__name__)

class ComprehensiveDatabaseManager:
    """Manages access to the comprehensive CS2 skins database"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Path("data/comprehensive_skins.db")
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Comprehensive database not found at {self.db_path}")
    
    def get_all_tradeable_skins(self) -> List[Dict]:
        """Get all skins that can be used in trade-ups (Consumer to Classified)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get skins that can be traded up (Consumer Grade to Classified)
        tradeable_rarities = [
            'Consumer Grade',
            'Industrial Grade', 
            'Mil-Spec Grade',
            'Restricted',
            'Classified'
        ]
        
        placeholders = ','.join(['?' for _ in tradeable_rarities])        
        query = f"""
            SELECT 
                market_hash_name, weapon_name, skin_name, condition_name,
                rarity, collection, weapon_category, stattrak, souvenir,
                min_float, max_float
            FROM comprehensive_skins 
            WHERE rarity IN ({placeholders})
            AND weapon_name IS NOT NULL
            AND skin_name IS NOT NULL
            AND souvenir = 0
            ORDER BY weapon_name, rarity, condition_name
        """
        
        cursor.execute(query, tradeable_rarities)
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_possible_outputs(self, input_rarity: str) -> List[Dict]:
        """Get possible trade-up outputs for a given input rarity"""
        rarity_progression = {
            'Consumer Grade': 'Industrial Grade',
            'Industrial Grade': 'Mil-Spec Grade',
            'Mil-Spec Grade': 'Restricted',
            'Restricted': 'Classified',
            'Classified': 'Covert'
        }
        
        output_rarity = rarity_progression.get(input_rarity)
        if not output_rarity:
            return []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT 
                market_hash_name, weapon_name, skin_name, condition_name,
                rarity, collection, weapon_category, stattrak, souvenir,
                min_float, max_float
            FROM comprehensive_skins 
            WHERE rarity = ?
            AND weapon_name IS NOT NULL
            AND skin_name IS NOT NULL
            AND souvenir = 0
            ORDER BY collection, weapon_name
        """
        
        cursor.execute(query, (output_rarity,))
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_skins_by_collection_and_rarity(self, collection: str, rarity: str) -> List[Dict]:
        """Get all skins in a specific collection and rarity"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT 
                market_hash_name, weapon_name, skin_name, condition_name,
                rarity, collection, weapon_category, stattrak, souvenir,
                min_float, max_float
            FROM comprehensive_skins 
            WHERE collection = ? AND rarity = ?
            AND weapon_name IS NOT NULL
            AND skin_name IS NOT NULL
            ORDER BY weapon_name, condition_name
        """
        
        cursor.execute(query, (collection, rarity))
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_collections_by_rarity(self, rarity: str) -> List[str]:
        """Get all collections that have skins of a specific rarity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT DISTINCT collection
            FROM comprehensive_skins 
            WHERE rarity = ?
            AND collection IS NOT NULL
            AND collection != 'Unknown'
            ORDER BY collection
        """
        
        cursor.execute(query, (rarity,))
        results = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in results]
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database contents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total skins
        cursor.execute("SELECT COUNT(*) FROM comprehensive_skins")
        stats['total_skins'] = cursor.fetchone()[0]
        
        # Unique weapons
        cursor.execute("SELECT COUNT(DISTINCT weapon_name) FROM comprehensive_skins WHERE weapon_name IS NOT NULL")
        stats['unique_weapons'] = cursor.fetchone()[0]
        
        # Unique collections
        cursor.execute("SELECT COUNT(DISTINCT collection) FROM comprehensive_skins WHERE collection IS NOT NULL AND collection != 'Unknown'")
        stats['unique_collections'] = cursor.fetchone()[0]
        
        # Skins by rarity
        cursor.execute("""
            SELECT rarity, COUNT(*) 
            FROM comprehensive_skins 
            WHERE rarity IS NOT NULL 
            GROUP BY rarity 
            ORDER BY COUNT(*) DESC
        """)
        stats['by_rarity'] = dict(cursor.fetchall())
        
        # Skins by weapon category
        cursor.execute("""
            SELECT weapon_category, COUNT(*) 
            FROM comprehensive_skins 
            WHERE weapon_category IS NOT NULL 
            GROUP BY weapon_category 
            ORDER BY COUNT(*) DESC
        """)
        stats['by_category'] = dict(cursor.fetchall())
        
        conn.close()
        return stats
    
    def get_skin_by_name(self, market_hash_name: str) -> Optional[Dict]:
        """Get a specific skin by its market hash name"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT *
            FROM comprehensive_skins 
            WHERE market_hash_name = ?
        """
        
        cursor.execute(query, (market_hash_name,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    def build_market_data_from_comprehensive(self, pricing_data: Dict[str, Decimal]) -> MarketData:
        """Build MarketData object from comprehensive database + runtime pricing"""
        all_skins = self.get_all_tradeable_skins()
        
        collections = {}
        
        for skin_data in all_skins:
            market_name = skin_data['market_hash_name']
            
            # Get runtime price or use default
            price = pricing_data.get(market_name, Decimal('0.50'))
            
            # Create Skin object
            skin = Skin(
                name=market_name,
                collection=skin_data.get('collection', 'Unknown'),
                rarity=skin_data['rarity'],
                price=price,
                float_min=skin_data['min_float'],
                float_max=skin_data['max_float'],
                marketable=True,                stattrak=bool(skin_data.get('stattrak', False))
            )
            
            # Build collection info
            collection_name = skin.collection
            if collection_name not in collections:
                collections[collection_name] = CollectionInfo(
                    name=collection_name,
                    skins_by_rarity={}
                )
            
            # Add skin to collection's rarity group
            if skin.rarity not in collections[collection_name].skins_by_rarity:
                collections[collection_name].skins_by_rarity[skin.rarity] = []
            collections[collection_name].skins_by_rarity[skin.rarity].append(skin)
        return MarketData(
            collections=collections,
            last_updated=0  # Will be set when pricing is fetched
        )
    
    def add_price_validation_columns_if_needed(self):
        """Add price validation tracking columns if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(comprehensive_skins)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add columns if they don't exist
        if 'price_validation_status' not in columns:
            cursor.execute("""
                ALTER TABLE comprehensive_skins 
                ADD COLUMN price_validation_status TEXT DEFAULT 'unvalidated'
            """)
            logger.info("Added price_validation_status column")
        
        if 'price_discrepancy_percent' not in columns:
            cursor.execute("""
                ALTER TABLE comprehensive_skins 
                ADD COLUMN price_discrepancy_percent REAL DEFAULT NULL
            """)
            logger.info("Added price_discrepancy_percent column")
        
        if 'last_price_check' not in columns:
            cursor.execute("""
                ALTER TABLE comprehensive_skins 
                ADD COLUMN last_price_check TIMESTAMP DEFAULT NULL
            """)
            logger.info("Added last_price_check column")
        
        if 'steam_price' not in columns:
            cursor.execute("""
                ALTER TABLE comprehensive_skins 
                ADD COLUMN steam_price REAL DEFAULT NULL
            """)
            logger.info("Added steam_price column")
        
        if 'last_steam_check' not in columns:
            cursor.execute("""
                ALTER TABLE comprehensive_skins 
                ADD COLUMN last_steam_check TIMESTAMP DEFAULT NULL
            """)
            logger.info("Added last_steam_check column")
        
        conn.commit()
        conn.close()
    
    def mark_price_discrepancy(self, market_hash_name: str, discrepancy_percent: float, status: str = 'invalid'):
        """Mark a skin as having a price discrepancy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE comprehensive_skins 
            SET price_validation_status = ?, 
                price_discrepancy_percent = ?,
                last_price_check = CURRENT_TIMESTAMP
            WHERE market_hash_name = ?
        """, (status, discrepancy_percent, market_hash_name))
        
        conn.commit()
        conn.close()
        logger.debug(f"Marked {market_hash_name} as {status} with {discrepancy_percent:.1f}% discrepancy")
    
    def mark_price_valid(self, market_hash_name: str):
        """Mark a skin as having valid pricing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE comprehensive_skins 
            SET price_validation_status = 'valid',
                price_discrepancy_percent = NULL,
                last_price_check = CURRENT_TIMESTAMP
            WHERE market_hash_name = ?
        """, (market_hash_name,))
        
        conn.commit()
        conn.close()
        logger.debug(f"Marked {market_hash_name} as having valid pricing")
    
    def mark_price_validation_status(self, market_hash_name: str, status: str, steam_price: float = None, 
                                       discrepancy_percent: float = None) -> None:
        """Mark a skin's price validation status to avoid repeated Steam API calls"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            UPDATE comprehensive_skins 
            SET price_validation_status = ?, 
                steam_price = ?, 
                price_discrepancy_percent = ?,
                last_steam_check = CURRENT_TIMESTAMP
            WHERE market_hash_name = ?
        """
        
        cursor.execute(query, (status, steam_price, discrepancy_percent, market_hash_name))
        conn.commit()
        conn.close()
        
        logger.debug(f"Marked {market_hash_name} as {status}")
    
    def get_price_validation_status(self, market_hash_name: str) -> Optional[Dict]:
        """Get price validation status for a skin"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT price_validation_status, steam_price, price_discrepancy_percent, last_steam_check
            FROM comprehensive_skins 
            WHERE market_hash_name = ?
        """
        
        cursor.execute(query, (market_hash_name,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'status': result['price_validation_status'] or 'unvalidated',
                'steam_price': result['steam_price'],
                'discrepancy_percent': result['price_discrepancy_percent'],
                'last_check': result['last_steam_check']
            }
        return None
    
    def get_skins_needing_validation(self, limit: int = 100) -> List[Dict]:
        """Get skins that need price validation (unvalidated or old validations)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get skins that either:
        # 1. Have never been validated
        # 2. Were last checked more than 7 days ago (for good skins)
        # 3. Exclude skins marked as 'invalid' (large discrepancy) unless very old
        query = """
            SELECT market_hash_name, rarity, current_price, price_validation_status, last_steam_check
            FROM comprehensive_skins 
            WHERE (
                price_validation_status IS NULL 
                OR price_validation_status = 'unvalidated'
                OR (price_validation_status = 'valid' AND date(last_steam_check) < date('now', '-7 days'))
            )
            AND souvenir = 0  -- Exclude souvenir skins
            AND current_price > 0
            ORDER BY 
                CASE 
                    WHEN price_validation_status IS NULL THEN 1
                    WHEN price_validation_status = 'unvalidated' THEN 2
                    ELSE 3
                END,
                current_price DESC
            LIMIT ?
        """
        
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
