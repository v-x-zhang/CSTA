"""
Steam Market Pricing Client for CS2 Trade-up Calculator
Provides alternative pricing source using Steam Market API
"""

import asyncio
import aiohttp
import logging
import time
import json
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import urllib.parse

logger = logging.getLogger(__name__)

class SteamMarketPricingClient:
    """Fetches pricing data from Steam Market API"""
    
    def __init__(self):
        self.base_url = "https://steamcommunity.com/market/priceoverview/"
        self.app_id = "730"  # CS2 App ID
        self.currency = "1"  # USD
        self.country = "US"
        self.rate_limit_delay = 1.1  # Steam has rate limits
        self._cache = {}
        self._session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'CS2 Trade-up Calculator'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
    
    async def get_price(self, market_hash_name: str) -> Optional[float]:
        """Get price for a single item from Steam Market"""
        
        if market_hash_name in self._cache:
            return self._cache[market_hash_name]
        
        if not self._session:
            raise RuntimeError("Must use async context manager (async with)")
        
        params = {
            'country': self.country,
            'currency': self.currency,
            'appid': self.app_id,
            'market_hash_name': market_hash_name
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            
            async with self._session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"Steam API returned {response.status} for {market_hash_name}")
                    return None
                
                data = await response.json()
                
                if not data.get('success'):
                    logger.debug(f"Steam API success=False for {market_hash_name}")
                    return None
                
                # Parse price from Steam format (e.g., "$1.23")
                lowest_price = data.get('lowest_price')
                if lowest_price:
                    # Remove currency symbol and convert to float
                    price_str = lowest_price.replace('$', '').replace(',', '')
                    try:
                        price = float(price_str)
                        self._cache[market_hash_name] = price
                        logger.debug(f"Got Steam price for {market_hash_name}: ${price:.2f}")
                        return price
                    except ValueError:
                        logger.warning(f"Could not parse price '{lowest_price}' for {market_hash_name}")
                        return None
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Steam price for {market_hash_name}: {e}")
            return None
    
    async def get_prices_batch(self, market_hash_names: List[str], max_concurrent: int = 5) -> Dict[str, float]:
        """Get prices for multiple items with concurrency control"""
        
        logger.info(f"Fetching Steam prices for {len(market_hash_names)} items...")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_single(name):
            async with semaphore:
                price = await self.get_price(name)
                return name, price
        
        # Execute all requests
        tasks = [fetch_single(name) for name in market_hash_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        prices = {}
        successful = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch fetch error: {result}")
                continue
            
            name, price = result
            if price is not None:
                prices[name] = price
                successful += 1
        
        logger.info(f"Successfully fetched {successful}/{len(market_hash_names)} Steam prices")
        return prices
    
    async def get_all_prices_for_skins(self, skin_names: List[str]) -> Dict[str, float]:
        """Get Steam Market prices for all provided skin names"""
        
        logger.info(f"Building Steam Market pricing database for {len(skin_names)} skins...")
        
        # Filter out duplicates
        unique_names = list(set(skin_names))
        logger.info(f"Fetching prices for {len(unique_names)} unique items...")
        
        # Fetch prices in batches to avoid overwhelming Steam API
        batch_size = 50
        all_prices = {}
        
        for i in range(0, len(unique_names), batch_size):
            batch = unique_names[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(unique_names) + batch_size - 1)//batch_size}")
            
            batch_prices = await self.get_prices_batch(batch)
            all_prices.update(batch_prices)
            
            # Progress update
            logger.info(f"Progress: {len(all_prices)}/{len(unique_names)} prices collected")
        
        logger.info(f"Steam Market pricing complete: {len(all_prices)} prices collected")
        return all_prices
    
    def get_cached_prices(self) -> Dict[str, float]:
        """Get all cached prices"""
        return self._cache.copy()
    
    def clear_cache(self):
        """Clear the price cache"""
        self._cache.clear()
        logger.info("Steam Market price cache cleared")

class SteamPricingAdapter:
    """Adapter to make Steam pricing compatible with existing RuntimePricingClient interface"""
    
    def __init__(self):
        self.steam_client = SteamMarketPricingClient()
        self._prices_cache = {}
        self._initialized = False
    
    async def get_all_prices(self) -> Dict[str, float]:
        """Get all prices - requires prior initialization with skin list"""
        if not self._initialized:
            raise RuntimeError("Must call initialize_with_skins() first")
        
        return self._prices_cache.copy()
    
    async def get_sample_prices(self, limit: int = 1000) -> Dict[str, float]:
        """Get sample of prices"""
        all_prices = await self.get_all_prices()
        items = list(all_prices.items())[:limit]
        return dict(items)
    
    async def initialize_with_skins(self, skin_names: List[str]) -> None:
        """Initialize the Steam pricing with a list of skin names"""
        
        async with self.steam_client:
            self._prices_cache = await self.steam_client.get_all_prices_for_skins(skin_names)
            self._initialized = True
        
        logger.info(f"Steam pricing adapter initialized with {len(self._prices_cache)} prices")
    
    async def fetch_prices(self, item_names: List[str]) -> Dict[str, float]:
        """Fetch prices for specific items"""
        async with self.steam_client:
            return await self.steam_client.get_prices_batch(item_names)
    
    def get_cached_price(self, item_name: str) -> Optional[float]:
        """Get cached price for an item"""
        return self._prices_cache.get(item_name)

# Steam database integration client
class SteamPricingClient:
    """Client that uses the Steam pricing database as a pricing source"""
    
    def __init__(self, db_path: str = None):
        from pathlib import Path
        self.db_path = db_path or Path("data/steam_pricing.db")
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Steam pricing database not found at {self.db_path}. Run build_steam_pricing_database.py first.")
    
    async def get_all_prices(self) -> Dict[str, float]:
        """Get all available Steam prices from database"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT market_hash_name, steam_price
            FROM steam_prices 
            WHERE success = 1 AND steam_price IS NOT NULL
        """)
        
        prices = dict(cursor.fetchall())
        conn.close()
        
        logger.info(f"Loaded {len(prices)} Steam prices from database")
        return prices
    
    async def get_sample_prices(self, limit: int = 1000) -> Dict[str, float]:
        """Get sample of Steam prices from database"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT market_hash_name, steam_price
            FROM steam_prices 
            WHERE success = 1 AND steam_price IS NOT NULL
            ORDER BY RANDOM()
            LIMIT ?
        """, (limit,))
        
        prices = dict(cursor.fetchall())
        conn.close()
        
        logger.info(f"Loaded {len(prices)} sample Steam prices from database")
        return prices
    
    async def fetch_prices_for_items(self, item_names: List[str]) -> Dict[str, float]:
        """Fetch prices for specific items from database"""
        import sqlite3
        
        if not item_names:
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create placeholders for the query
        placeholders = ','.join(['?' for _ in item_names])
        
        cursor.execute(f"""
            SELECT market_hash_name, steam_price
            FROM steam_prices 
            WHERE market_hash_name IN ({placeholders})
            AND success = 1 AND steam_price IS NOT NULL
        """, item_names)
        
        prices = dict(cursor.fetchall())
        conn.close()
        
        logger.debug(f"Fetched {len(prices)}/{len(item_names)} Steam prices for specific items")
        return prices
    
    async def validate_and_correct_price(self, market_hash_name: str, external_price: float, 
                                       rarity: str, tolerance_percent: float = 20.0) -> Optional[float]:
        """Validate external price against Steam price"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT steam_price
            FROM steam_prices 
            WHERE market_hash_name = ? AND success = 1 AND steam_price IS NOT NULL
        """, (market_hash_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            steam_price = float(result[0])
            # For Steam pricing client, always prefer Steam price as authoritative
            logger.debug(f"Using Steam price ${steam_price:.2f} for {market_hash_name}")
            return steam_price
        else:
            logger.debug(f"No Steam price found for {market_hash_name}")
            return None
    
    def get_pricing_stats(self) -> Dict:
        """Get statistics about the Steam pricing database"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total successful prices
        cursor.execute("SELECT COUNT(*) FROM steam_prices WHERE success = 1")
        stats['total_prices'] = cursor.fetchone()[0]
        
        # Average price
        cursor.execute("SELECT AVG(steam_price) FROM steam_prices WHERE success = 1 AND steam_price IS NOT NULL")
        avg_price = cursor.fetchone()[0]
        stats['average_price'] = float(avg_price) if avg_price else 0.0
        
        conn.close()
        return stats

# Test function
async def test_steam_pricing():
    """Test the Steam pricing client"""
    
    print("🧪 Testing Steam Market Pricing Client")
    print("=" * 50)
    
    # Test with some common CS2 items
    test_items = [
        "AK-47 | Blue Laminate (Field-Tested)",
        "M4A4 | Desolate Space (Minimal Wear)",
        "AWP | Pit Viper (Field-Tested)",
        "Glock-18 | Water Elemental (Factory New)",
        "USP-S | Kill Confirmed (Battle-Scarred)"
    ]
    
    async with SteamMarketPricingClient() as client:
        print(f"\n🔍 Testing individual price fetches:")
        
        for item in test_items:
            price = await client.get_price(item)
            if price:
                print(f"   ✅ {item}: ${price:.2f}")
            else:
                print(f"   ❌ {item}: No price found")
        
        print(f"\n🔍 Testing batch price fetch:")
        batch_prices = await client.get_prices_batch(test_items)
        
        print(f"   Batch results: {len(batch_prices)}/{len(test_items)} successful")
        for item, price in batch_prices.items():
            print(f"   {item}: ${price:.2f}")
    
    print(f"\n✅ Steam pricing test complete!")

if __name__ == "__main__":
    asyncio.run(test_steam_pricing())
