"""
Steam Pricing Database Builder for CS2 Trade-up Calculator
Builds a comprehensive pricing database using Steam Market API
"""

import asyncio
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.logging_config import setup_logging
from src.steam_pricing import SteamMarketPricingClient
from src.comprehensive_database import ComprehensiveDatabaseManager

logger = logging.getLogger(__name__)

class SteamPricingDatabaseBuilder:
    """Builds a Steam Market pricing database for CS2 skins"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Path("data/steam_pricing.db")
        self.comprehensive_db = ComprehensiveDatabaseManager()
        
    def init_database(self):
        """Initialize the Steam pricing database"""
        logger.info("Initializing Steam pricing database...")
        
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing table if it exists
        cursor.execute("DROP TABLE IF EXISTS steam_prices")
        cursor.execute("DROP TABLE IF EXISTS pricing_metadata")
        
        # Create steam prices table
        cursor.execute("""
            CREATE TABLE steam_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_hash_name TEXT UNIQUE NOT NULL,
                steam_price REAL,
                success BOOLEAN DEFAULT FALSE,
                last_fetched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                attempts INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create metadata table
        cursor.execute("""
            CREATE TABLE pricing_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX idx_market_hash_name ON steam_prices(market_hash_name)")
        cursor.execute("CREATE INDEX idx_last_fetched ON steam_prices(last_fetched)")
        cursor.execute("CREATE INDEX idx_success ON steam_prices(success)")
        
        conn.commit()
        conn.close()
        
        logger.info("Steam pricing database initialized successfully")
    
    def get_all_skin_names(self) -> List[str]:
        """Get all skin names from the comprehensive database"""
        logger.info("Getting all skin names from comprehensive database...")
        
        # Get all tradeable skins
        all_skins = self.comprehensive_db.get_all_tradeable_skins()
        
        # Extract unique market hash names
        skin_names = list(set(skin['market_hash_name'] for skin in all_skins))
        
        # Filter out souvenir and stattrak items (can't be traded up)
        filtered_names = []
        for name in skin_names:
            if 'Souvenir' not in name and 'StatTrak™' not in name:
                filtered_names.append(name)
        
        logger.info(f"Found {len(filtered_names)} unique tradeable skin names")
        return filtered_names
    
    def get_pending_skins(self) -> List[str]:
        """Get skins that haven't been successfully priced yet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all skin names that need pricing
        all_names = self.get_all_skin_names()
        
        # Check which ones we've already successfully priced
        cursor.execute("""
            SELECT market_hash_name 
            FROM steam_prices 
            WHERE success = 1 AND steam_price IS NOT NULL
        """)
        
        successfully_priced = set(row[0] for row in cursor.fetchall())
        conn.close()
        
        # Return names that still need pricing
        pending = [name for name in all_names if name not in successfully_priced]
        
        logger.info(f"Found {len(pending)} skins pending Steam pricing")
        return pending
    
    def save_prices(self, prices: Dict[str, float], failed_items: List[str] = None):
        """Save Steam prices to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save successful prices
        for market_hash_name, price in prices.items():
            cursor.execute("""
                INSERT OR REPLACE INTO steam_prices 
                (market_hash_name, steam_price, success, last_fetched, attempts)
                VALUES (?, ?, ?, ?, COALESCE((SELECT attempts FROM steam_prices WHERE market_hash_name = ?), 0) + 1)
            """, (market_hash_name, price, True, datetime.utcnow().isoformat(), market_hash_name))
        
        # Save failed items
        if failed_items:
            for market_hash_name in failed_items:
                cursor.execute("""
                    INSERT OR REPLACE INTO steam_prices 
                    (market_hash_name, steam_price, success, last_fetched, attempts, error_message)
                    VALUES (?, ?, ?, ?, COALESCE((SELECT attempts FROM steam_prices WHERE market_hash_name = ?), 0) + 1, ?)
                """, (market_hash_name, None, False, datetime.utcnow().isoformat(), market_hash_name, "No price available"))
        
        # Update metadata
        cursor.execute("""
            INSERT OR REPLACE INTO pricing_metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ('last_update', datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        cursor.execute("""
            INSERT OR REPLACE INTO pricing_metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ('total_successful', str(len(prices)), datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved {len(prices)} successful prices and {len(failed_items or [])} failed items")
    
    def get_pricing_stats(self) -> Dict:
        """Get statistics about the Steam pricing database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total items
        cursor.execute("SELECT COUNT(*) FROM steam_prices")
        stats['total_items'] = cursor.fetchone()[0]
        
        # Successful prices
        cursor.execute("SELECT COUNT(*) FROM steam_prices WHERE success = 1")
        stats['successful_prices'] = cursor.fetchone()[0]
        
        # Failed items
        cursor.execute("SELECT COUNT(*) FROM steam_prices WHERE success = 0")
        stats['failed_items'] = cursor.fetchone()[0]
        
        # Average price
        cursor.execute("SELECT AVG(steam_price) FROM steam_prices WHERE success = 1 AND steam_price IS NOT NULL")
        avg_price = cursor.fetchone()[0]
        stats['average_price'] = float(avg_price) if avg_price else 0.0
        
        # Price range
        cursor.execute("SELECT MIN(steam_price), MAX(steam_price) FROM steam_prices WHERE success = 1 AND steam_price IS NOT NULL")
        min_price, max_price = cursor.fetchone()
        stats['min_price'] = float(min_price) if min_price else 0.0
        stats['max_price'] = float(max_price) if max_price else 0.0
        
        # Last update
        cursor.execute("SELECT value FROM pricing_metadata WHERE key = 'last_update'")
        last_update = cursor.fetchone()
        stats['last_update'] = last_update[0] if last_update else 'Never'
        
        conn.close()
        return stats
    
    def get_all_steam_prices(self) -> Dict[str, float]:
        """Get all successfully fetched Steam prices"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT market_hash_name, steam_price
            FROM steam_prices 
            WHERE success = 1 AND steam_price IS NOT NULL
        """)
        
        prices = dict(cursor.fetchall())
        conn.close()
        
        return prices
    
    async def build_pricing_database(self, batch_size: int = 50, max_concurrent: int = 5):
        """Build the Steam pricing database"""
        logger.info("Starting Steam pricing database build...")
        
        # Initialize database
        self.init_database()
        
        # Get all skin names that need pricing
        pending_skins = self.get_pending_skins()
        
        if not pending_skins:
            logger.info("All skins already have pricing data!")
            return
        
        logger.info(f"Fetching Steam prices for {len(pending_skins)} skins...")
        
        # Fetch prices in batches using Steam client
        async with SteamMarketPricingClient() as steam_client:
            total_processed = 0
            total_successful = 0
            
            for i in range(0, len(pending_skins), batch_size):
                batch = pending_skins[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(pending_skins) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
                
                # Fetch prices for this batch
                batch_prices = await steam_client.get_prices_batch(batch, max_concurrent)
                
                # Determine failed items
                failed_items = [name for name in batch if name not in batch_prices]
                
                # Save to database
                self.save_prices(batch_prices, failed_items)
                
                # Update counters
                total_processed += len(batch)
                total_successful += len(batch_prices)
                
                logger.info(f"Batch {batch_num} complete: {len(batch_prices)}/{len(batch)} successful")
                logger.info(f"Overall progress: {total_processed}/{len(pending_skins)} processed, {total_successful} successful")
        
        logger.info("Steam pricing database build complete!")
        
        # Show final stats
        stats = self.get_pricing_stats()
        self.print_pricing_summary(stats)
    
    def print_pricing_summary(self, stats: Dict = None):
        """Print summary of Steam pricing database"""
        if stats is None:
            stats = self.get_pricing_stats()
        
        print("\n" + "="*60)
        print("           STEAM PRICING DATABASE SUMMARY")
        print("="*60)
        print(f"Total Items: {stats['total_items']:,}")
        print(f"Successful Prices: {stats['successful_prices']:,}")
        print(f"Failed Items: {stats['failed_items']:,}")
        print(f"Success Rate: {(stats['successful_prices'] / max(1, stats['total_items']) * 100):.1f}%")
        print(f"Average Price: ${stats['average_price']:.2f}")
        print(f"Price Range: ${stats['min_price']:.2f} - ${stats['max_price']:.2f}")
        print(f"Last Update: {stats['last_update']}")
        print("="*60)

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build Steam Market pricing database for CS2 skins')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Number of items to process per batch (default: 50)')
    parser.add_argument('--max-concurrent', type=int, default=5,
                       help='Maximum concurrent requests to Steam API (default: 5)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Show statistics without building database')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    try:
        builder = SteamPricingDatabaseBuilder()
        
        if args.stats_only:
            print("📊 Steam Pricing Database Statistics")
            try:
                stats = builder.get_pricing_stats()
                builder.print_pricing_summary(stats)
            except Exception as e:
                print(f"❌ Error getting stats: {e}")
                print("💡 Run without --stats-only to build the database first")
        else:
            print("🔄 Building Steam Market pricing database...")
            await builder.build_pricing_database(
                batch_size=args.batch_size,
                max_concurrent=args.max_concurrent
            )
            print("✅ Steam pricing database build complete!")
        
    except KeyboardInterrupt:
        print("\n🛑 Build cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
