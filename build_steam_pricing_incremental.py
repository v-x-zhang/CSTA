"""
Incremental Steam Pricing Database Builder for CS2 Trade-up Calculator
Builds Steam pricing database gradually with strict rate limiting (200 requests per 5 minutes)
"""

import asyncio
import sqlite3
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.logging_config import setup_logging
from src.steam_pricing import SteamMarketPricingClient
from src.comprehensive_database import ComprehensiveDatabaseManager

logger = logging.getLogger(__name__)

class RateLimitedSteamPricingBuilder:
    """
    Builds Steam pricing database with strict rate limiting
    Limits to 200 requests per 5-minute window to respect Steam API limits
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Path("data/steam_pricing.db")
        self.comprehensive_db = ComprehensiveDatabaseManager()
        
        # Rate limiting configuration
        self.max_requests_per_window = 200
        self.window_duration_seconds = 6 * 60  # 6 minutes
        self.request_delay = 1.8  # Minimum delay between requests (seconds)
        
        # Track request timing
        self.request_times = []
        self.session_start_time = None
        
    def init_database(self):
        """Initialize the Steam pricing database"""
        logger.info("Initializing Steam pricing database...")
        
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create steam prices table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS steam_prices (
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
        
        # Create metadata table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pricing_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_hash_name ON steam_prices(market_hash_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_fetched ON steam_prices(last_fetched)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_success ON steam_prices(success)")
        
        conn.commit()
        conn.close()
        
        logger.info("Steam pricing database initialized successfully")
    
    def can_make_request(self) -> Tuple[bool, float]:
        """
        Check if we can make another request within rate limits
        Returns (can_make_request, wait_time_seconds)
        """
        current_time = time.time()
        
        # Clean old request times outside the window
        cutoff_time = current_time - self.window_duration_seconds
        self.request_times = [t for t in self.request_times if t > cutoff_time]
        
        # Check if we're at the limit
        if len(self.request_times) >= self.max_requests_per_window:
            # Calculate wait time until oldest request expires
            oldest_request = min(self.request_times)
            wait_time = (oldest_request + self.window_duration_seconds) - current_time
            return False, max(0, wait_time)
        
        # Check minimum delay since last request
        if self.request_times:
            time_since_last = current_time - max(self.request_times)
            if time_since_last < self.request_delay:
                wait_time = self.request_delay - time_since_last
                return False, wait_time
        
        return True, 0
    
    def record_request(self):
        """Record that a request was made"""
        self.request_times.append(time.time())
    
    def get_pending_skins(self, limit: int = None) -> List[str]:
        """Get skins that haven't been successfully priced yet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all skin names from comprehensive database
        all_skins = self.comprehensive_db.get_all_tradeable_skins()
        all_names = list(set(skin['market_hash_name'] for skin in all_skins))
        
        # Filter out souvenir and stattrak items (can't be traded up)
        filtered_names = []
        for name in all_names:
            if 'Souvenir' not in name and 'StatTrak™' not in name:
                filtered_names.append(name)
        
        # Check which ones we've already successfully priced
        cursor.execute("""
            SELECT market_hash_name 
            FROM steam_prices 
            WHERE success = 1 AND steam_price IS NOT NULL
        """)
        
        successfully_priced = set(row[0] for row in cursor.fetchall())
        conn.close()
        
        # Return names that still need pricing
        pending = [name for name in filtered_names if name not in successfully_priced]
        
        if limit:
            pending = pending[:limit]
        
        logger.info(f"Found {len(pending)} skins pending Steam pricing")
        return pending
    
    def save_price(self, market_hash_name: str, price: Optional[float], success: bool, error_message: str = None):
        """Save a single Steam price to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO steam_prices 
            (market_hash_name, steam_price, success, last_fetched, attempts, error_message)
            VALUES (?, ?, ?, ?, COALESCE((SELECT attempts FROM steam_prices WHERE market_hash_name = ?), 0) + 1, ?)
        """, (market_hash_name, price, success, datetime.utcnow().isoformat(), market_hash_name, error_message))
        
        conn.commit()
        conn.close()
    
    def update_session_metadata(self, processed_count: int, successful_count: int):
        """Update session metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update last session info
        cursor.execute("""
            INSERT OR REPLACE INTO pricing_metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ('last_session_processed', str(processed_count), datetime.utcnow().isoformat()))
        
        cursor.execute("""
            INSERT OR REPLACE INTO pricing_metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ('last_session_successful', str(successful_count), datetime.utcnow().isoformat()))
        
        cursor.execute("""
            INSERT OR REPLACE INTO pricing_metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """, ('last_update', datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_pricing_stats(self) -> Dict:
        """Get statistics about the Steam pricing database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total items in database
        cursor.execute("SELECT COUNT(*) FROM steam_prices")
        stats['total_items'] = cursor.fetchone()[0]
        
        # Successful prices
        cursor.execute("SELECT COUNT(*) FROM steam_prices WHERE success = 1")
        stats['successful_prices'] = cursor.fetchone()[0]
        
        # Failed items
        cursor.execute("SELECT COUNT(*) FROM steam_prices WHERE success = 0")
        stats['failed_items'] = cursor.fetchone()[0]
        
        # Pending items (total possible - successfully priced)
        all_skins = self.comprehensive_db.get_all_tradeable_skins()
        all_names = list(set(skin['market_hash_name'] for skin in all_skins))
        filtered_names = [name for name in all_names if 'Souvenir' not in name and 'StatTrak™' not in name]
        stats['total_possible'] = len(filtered_names)
        stats['pending_items'] = stats['total_possible'] - stats['successful_prices']
        
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
        
        # Session info
        cursor.execute("SELECT value FROM pricing_metadata WHERE key = 'last_session_processed'")
        last_processed = cursor.fetchone()
        stats['last_session_processed'] = int(last_processed[0]) if last_processed else 0
        
        cursor.execute("SELECT value FROM pricing_metadata WHERE key = 'last_session_successful'")
        last_successful = cursor.fetchone()
        stats['last_session_successful'] = int(last_successful[0]) if last_successful else 0
        
        conn.close()
        return stats
    
    async def build_incremental_batch(self, max_items: int = None) -> Dict:
        """
        Build Steam pricing database incrementally with strict rate limiting
        Returns session statistics
        """
        logger.info("Starting incremental Steam pricing build...")
        
        # Initialize database
        self.init_database()
        
        # Determine how many items to process
        if max_items is None:
            # Use rate limit as default (leave some buffer)
            max_items = min(180, self.max_requests_per_window - 20)
        
        # Get pending skins to process
        pending_skins = self.get_pending_skins(limit=max_items)
        
        if not pending_skins:
            logger.info("All skins already have pricing data!")
            return {"processed": 0, "successful": 0, "reason": "complete"}
        
        actual_to_process = min(len(pending_skins), max_items)
        skins_to_process = pending_skins[:actual_to_process]
        
        logger.info(f"Processing {len(skins_to_process)} skins with rate limiting...")
        logger.info(f"Rate limit: {self.max_requests_per_window} requests per {self.window_duration_seconds//60} minutes")
        
        # Process items one by one with rate limiting
        self.session_start_time = time.time()
        processed_count = 0
        successful_count = 0
        
        async with SteamMarketPricingClient() as steam_client:
            for i, skin_name in enumerate(skins_to_process):
                # Check rate limits
                can_request, wait_time = self.can_make_request()
                
                if not can_request:
                    logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                    await asyncio.sleep(wait_time)
                
                # Make the request
                logger.info(f"[{i+1}/{len(skins_to_process)}] Fetching: {skin_name}")
                
                try:
                    price = await steam_client.get_price(skin_name)
                    self.record_request()
                    
                    if price is not None:
                        self.save_price(skin_name, price, success=True)
                        successful_count += 1
                        logger.info(f"${price:.2f}")
                    else:
                        self.save_price(skin_name, None, success=False, error_message="No price available")
                        logger.info(f"No price found")
                    
                    processed_count += 1
                    
                    # Show progress every 10 items
                    if (i + 1) % 10 == 0:
                        remaining_in_window = self.max_requests_per_window - len(self.request_times)
                        logger.info(f"Progress: {processed_count}/{len(skins_to_process)} processed, "
                                  f"{successful_count} successful, {remaining_in_window} requests remaining in window")
                
                except Exception as e:
                    logger.error(f"Error processing {skin_name}: {e}")
                    self.save_price(skin_name, None, success=False, error_message=str(e))
                    processed_count += 1
        
        # Update session metadata
        self.update_session_metadata(processed_count, successful_count)
        
        session_time = time.time() - self.session_start_time
        logger.info(f"Session complete in {session_time:.1f}s: {successful_count}/{processed_count} successful")
        
        return {
            "processed": processed_count,
            "successful": successful_count,
            "session_time": session_time,
            "reason": "session_complete"
        }
    
    def print_pricing_summary(self, stats: Dict = None):
        """Print summary of Steam pricing database"""
        if stats is None:
            stats = self.get_pricing_stats()
        
        print("\n" + "="*60)
        print("      INCREMENTAL STEAM PRICING DATABASE SUMMARY")
        print("="*60)
        print(f"Total Possible Items: {stats['total_possible']:,}")
        print(f"Successfully Priced: {stats['successful_prices']:,}")
        print(f"Failed Items: {stats['failed_items']:,}")
        print(f"Pending Items: {stats['pending_items']:,}")
        
        if stats['total_possible'] > 0:
            completion_pct = (stats['successful_prices'] / stats['total_possible']) * 100
            print(f"Completion: {completion_pct:.1f}%")
        
        print(f"Average Price: ${stats['average_price']:.2f}")
        print(f"Price Range: ${stats['min_price']:.2f} - ${stats['max_price']:.2f}")
        print(f"Last Update: {stats['last_update']}")
        print(f"Last Session: {stats['last_session_successful']}/{stats['last_session_processed']} successful")
        print("="*60)

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build Steam Market pricing database incrementally')
    parser.add_argument('--max-items', type=int, default=None,
                       help='Maximum items to process in this session (default: 180)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Show statistics without building database')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously until all items are processed')
    parser.add_argument('--delay-between-sessions', type=int, default=5,
                       help='Minutes to wait between sessions in continuous mode (default: 5)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    try:
        builder = RateLimitedSteamPricingBuilder()
        
        if args.stats_only:
            print("Incremental Steam Pricing Database Statistics")
            try:
                stats = builder.get_pricing_stats()
                builder.print_pricing_summary(stats)
            except Exception as e:
                print(f"Error getting stats: {e}")
                print("Run without --stats-only to build the database first")
            return
        
        if args.continuous:
            print("Starting continuous incremental build...")
            session_count = 0
            
            while True:
                session_count += 1
                print(f"\nStarting session {session_count}")
                
                session_result = await builder.build_incremental_batch(max_items=args.max_items)
                
                if session_result["reason"] == "complete":
                    print("All items have been processed!")
                    break
                
                print(f"Session {session_count} complete: {session_result['successful']}/{session_result['processed']} successful")
                
                # Show current stats
                stats = builder.get_pricing_stats()
                print(f"Overall progress: {stats['successful_prices']}/{stats['total_possible']} ({(stats['successful_prices']/stats['total_possible']*100):.1f}%)")
                
                if session_result["processed"] > 0:
                    wait_minutes = args.delay_between_sessions
                    print(f"Waiting {wait_minutes} minutes before next session...")
                    await asyncio.sleep(wait_minutes * 60)
                else:
                    print("No items processed. Ending continuous mode.")
                    break
        else:
            print("Running single incremental session...")
            session_result = await builder.build_incremental_batch(max_items=args.max_items)
            
            if session_result["reason"] == "complete":
                print("All items have been processed!")
            else:
                print(f"Session complete: {session_result['successful']}/{session_result['processed']} successful")
            
            # Show final stats
            stats = builder.get_pricing_stats()
            builder.print_pricing_summary(stats)
            
            if stats['pending_items'] > 0:
                print(f"\nTo continue building the database, run this script again.")
                print(f"Use --continuous to run until completion automatically.")
        
    except KeyboardInterrupt:
        print("\nBuild cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
