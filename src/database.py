"""
Database module for caching skin data and trade-up results
Uses SQLite for local storage with automatic schema management.
"""

import sqlite3
import time
import logging
from typing import List, Dict, Optional
from decimal import Decimal
from contextlib import contextmanager

from .config import config
from .models import Skin, MarketData, CollectionInfo

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database for caching skin data"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.database.DB_PATH
        self._ensure_db_directory()
        self._initialize_database()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        import os
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _initialize_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            # Enable WAL mode for better concurrent access
            if config.database.ENABLE_WAL:
                conn.execute("PRAGMA journal_mode=WAL")
              # Create tables
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS skins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    collection TEXT NOT NULL,
                    rarity TEXT NOT NULL,
                    price REAL NOT NULL,
                    float_min REAL NOT NULL,
                    float_max REAL NOT NULL,
                    marketable BOOLEAN NOT NULL DEFAULT 1,
                    stattrak BOOLEAN NOT NULL DEFAULT 0,
                    last_updated REAL NOT NULL,
                    UNIQUE(name, collection)
                );
                
                CREATE TABLE IF NOT EXISTS market_cache (
                    id INTEGER PRIMARY KEY,
                    last_updated REAL NOT NULL,
                    total_skins INTEGER NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_skins_collection_rarity 
                ON skins(collection, rarity);
                
                CREATE INDEX IF NOT EXISTS idx_skins_rarity_price 
                ON skins(rarity, price);
                
                CREATE INDEX IF NOT EXISTS idx_skins_last_updated 
                ON skins(last_updated);
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def cache_skins(self, skins: List[Skin]) -> None:
        """Cache skin data to database"""
        current_time = time.time()
        
        with self._get_connection() as conn:
            # Clear old data
            conn.execute("DELETE FROM skins")
            
            # Insert new data
            skin_data = [
                (
                    skin.name,
                    skin.collection,
                    skin.rarity,
                    float(skin.price),
                    skin.float_min,
                    skin.float_max,
                    skin.marketable,
                    skin.stattrak,
                    current_time
                )
                for skin in skins
            ]
            
            conn.executemany("""
                INSERT INTO skins (
                    name, collection, rarity, price, float_min, float_max,
                    marketable, stattrak, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, skin_data)
            
            # Update cache metadata
            conn.execute("DELETE FROM market_cache")
            conn.execute("""
                INSERT INTO market_cache (id, last_updated, total_skins)
                VALUES (1, ?, ?)
            """, (current_time, len(skins)))
            
            conn.commit()
            logger.info(f"Cached {len(skins)} skins to database")
    
    def load_cached_skins(self) -> Optional[List[Skin]]:
        """Load cached skin data from database"""
        with self._get_connection() as conn:
            # Check cache age
            cache_info = conn.execute("""
                SELECT last_updated, total_skins FROM market_cache WHERE id = 1
            """).fetchone()
            
            if not cache_info:
                logger.info("No cached data found")
                return None
            
            cache_age = time.time() - cache_info['last_updated']
            if cache_age > config.api.CACHE_REFRESH_INTERVAL:
                logger.info(f"Cache is {cache_age/60:.1f} minutes old, refresh needed")
                return None
            
            # Load skin data
            rows = conn.execute("""
                SELECT name, collection, rarity, price, float_min, float_max,
                       marketable, stattrak
                FROM skins
                ORDER BY collection, rarity, price
            """).fetchall()
            
            skins = []
            for row in rows:
                skin = Skin(
                    name=row['name'],
                    collection=row['collection'],
                    rarity=row['rarity'],
                    price=Decimal(str(row['price'])),
                    float_min=row['float_min'],
                    float_max=row['float_max'],
                    marketable=bool(row['marketable']),
                    stattrak=bool(row['stattrak'])
                )
                skins.append(skin)
            
            logger.info(f"Loaded {len(skins)} cached skins from database")
            return skins
    
    def build_market_data(self) -> Optional[MarketData]:
        """Build MarketData object from cached database"""
        skins = self.load_cached_skins()
        if not skins:
            return None
        
        # Group skins by collection and rarity
        collections = {}
        for skin in skins:
            if skin.collection not in collections:
                collections[skin.collection] = CollectionInfo(
                    name=skin.collection,
                    skins_by_rarity={}
                )
            
            collection = collections[skin.collection]
            if skin.rarity not in collection.skins_by_rarity:
                collection.skins_by_rarity[skin.rarity] = []
            
            collection.skins_by_rarity[skin.rarity].append(skin)
        
        # Sort skins within each rarity by price
        for collection in collections.values():
            for rarity_skins in collection.skins_by_rarity.values():
                rarity_skins.sort(key=lambda s: s.price)
        
        return MarketData(
            collections=collections,
            last_updated=time.time()
        )