"""
Runtime Pricing Client for CS2 Trade-up Calculator
Fetches current market prices for specific skins when needed
"""

import asyncio
import aiohttp
import logging
import statistics
import time
import numpy as np
import requests
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta

try:
    from .config import config
except ImportError:
    from config import config

logger = logging.getLogger(__name__)

class RuntimePricingClient:
    """Client for fetching current market prices at runtime"""
    
    def __init__(self):        
        self.base_url = config.api.PRICE_EMPIRE_BASE_URL
        self.headers = config.price_empire_headers
        
        # In-memory cache for all pricing data
        self._price_cache: Dict[str, Decimal] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=30)  # Cache for 30 minutes
        
    async def _ensure_price_cache_loaded(self) -> None:
        """Ensure the price cache is loaded and current"""
        now = datetime.now()
        
        # Check if cache needs refresh
        if (self._cache_timestamp is None or 
            now - self._cache_timestamp > self._cache_duration or
            not self._price_cache):
            
            logger.info("Loading/refreshing price cache...")
            await self._load_all_prices()
            self._cache_timestamp = now
        else:
            logger.debug(f"Using cached prices (loaded {(now - self._cache_timestamp).total_seconds():.0f}s ago)")
    
    async def _load_all_prices(self) -> None:
        """Load all prices from API into cache"""
        async with aiohttp.ClientSession() as session:
            params = {
                'app_id': 730,  # CS2
                'currency': 'USD',
                'language': 'en'
            }
            
            try:
                async with session.get(f"{self.base_url}/items/prices", 
                                     headers=self.headers, 
                                     params=params) as response:
                    
                    if response.status != 200:
                        logger.error(f"Price cache load failed: {response.status}")
                        return
                    
                    data = await response.json()
                    logger.info(f"Received price data for {len(data)} items")
                    
                    # Cache all prices
                    self._price_cache.clear()
                    
                    for item in data:
                        market_hash_name = item.get('market_hash_name', '')
                        if market_hash_name:
                            price = self._extract_best_price(item)
                            if price and price > 0:
                                self._price_cache[market_hash_name] = Decimal(str(price))
                    
                    logger.info(f"Cached prices for {len(self._price_cache)} items")
                    
            except Exception as e:
                logger.error(f"Error loading price cache: {e}")
        
    async def fetch_prices_for_items(self, item_names: List[str]) -> Dict[str, Decimal]:
        """Fetch current prices for a list of item names"""
        logger.info(f"Fetching prices for {len(item_names)} items from cache...")
        
        # Ensure cache is loaded
        await self._ensure_price_cache_loaded()
        
        # Extract requested prices from cache
        prices = {}
        for item_name in item_names:
            if item_name in self._price_cache:
                prices[item_name] = self._price_cache[item_name]
        
        logger.info(f"Found cached prices for {len(prices)}/{len(item_names)} items")
        
        # If we're missing some prices, they may be new items not in cache
        missing_items = set(item_names) - set(prices.keys())
        if missing_items:
            logger.debug(f"Missing prices for {len(missing_items)} items - may need cache refresh")
        
        return prices
    
    def _extract_best_price(self, item_data: Dict) -> Optional[float]:
        """Extract the best available price from item data"""
        prices = item_data.get('prices', [])
        if not prices:
            return None
        
        # Prefer Steam prices, then any reliable marketplace
        steam_price = None
        best_price = None
        
        for price_entry in prices:
            price = price_entry.get('price')
            provider = price_entry.get('provider_key', '')
            
            if not price or price <= 0:
                continue
                
            # Convert from cents to dollars if needed
            if price > 100:  # Likely in cents
                price = price / 100
            
            if provider == 'steam':
                steam_price = price
            elif not best_price:
                best_price = price
        
        return steam_price or best_price
    
    async def fetch_prices_for_trade_up(self, input_skins: List[str], output_skins: List[str]) -> Dict[str, Decimal]:
        """Fetch prices specifically for a trade-up calculation"""
        all_items = list(set(input_skins + output_skins))
        return await self.fetch_prices_for_items(all_items)
    async def get_sample_prices(self, limit: int = 100) -> Dict[str, Decimal]:
        """Get sample prices for testing (limited set)"""
        logger.info(f"Fetching sample prices (limit: {limit})...")
        
        # Ensure cache is loaded
        await self._ensure_price_cache_loaded()
        
        # Get a sample from cached prices
        prices = {}
        count = 0
        
        for market_hash_name, price in self._price_cache.items():
            if count >= limit:
                break
                
            if '|' in market_hash_name:  # Only weapon skins
                prices[market_hash_name] = price
                count += 1
        
        logger.info(f"Collected {len(prices)} sample prices from cache")
        return prices
    
    async def get_all_prices(self) -> Dict[str, Decimal]:
        """Get all available pricing data (no limit)"""
        logger.info("Fetching all available pricing data...")
        
        # Ensure cache is loaded
        await self._ensure_price_cache_loaded()
        
        # Get all weapon skin prices from cached data
        prices = {}
        
        for market_hash_name, price in self._price_cache.items():
            if '|' in market_hash_name:  # Only weapon skins
                prices[market_hash_name] = price
        
        logger.info(f"Collected {len(prices)} prices from complete cache")
        return prices
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cached_items': len(self._price_cache),
            'cache_age_seconds': (datetime.now() - self._cache_timestamp).total_seconds() if self._cache_timestamp else None,
            'cache_valid': self._cache_timestamp is not None and datetime.now() - self._cache_timestamp < self._cache_duration
        }
    
    async def force_refresh_cache(self) -> None:
        """Force refresh the price cache"""
        logger.info("Force refreshing price cache...")
        await self._load_all_prices()
        self._cache_timestamp = datetime.now()

    async def get_steam_market_price(self, market_hash_name: str, retries: int = 3) -> Optional[float]:
        """Get price directly from Steam Community Market API with retries"""
        url = "https://steamcommunity.com/market/priceoverview/"
        params = {
            'appid': 730,  # CS2
            'currency': 1,  # USD
            'market_hash_name': market_hash_name
        }
        
        for attempt in range(retries):
            try:
                # Add increasing delay between retries to avoid rate limiting
                if attempt > 0:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 429:
                            # Rate limited, wait longer
                            logger.debug(f"Rate limited on Steam API for {market_hash_name}, attempt {attempt + 1}")
                            if attempt < retries - 1:
                                await asyncio.sleep(5)
                                continue
                            return None
                        
                        if response.status != 200:
                            logger.debug(f"Steam API returned {response.status} for {market_hash_name}")
                            if attempt < retries - 1:
                                continue
                            return None
                        
                        data = await response.json()
                        
                        if data.get('success'):
                            # Try median price first, then lowest price
                            median_price = data.get('median_price', '').replace('$', '').replace(',', '')
                            lowest_price = data.get('lowest_price', '').replace('$', '').replace(',', '')
                            
                            # Prefer median price if available
                            if median_price:
                                try:
                                    price = float(median_price)
                                    logger.debug(f"Got Steam median price ${price:.2f} for {market_hash_name}")
                                    return price
                                except ValueError:
                                    pass
                            
                            # Fall back to lowest price
                            if lowest_price:
                                try:
                                    price = float(lowest_price)
                                    logger.debug(f"Got Steam lowest price ${price:.2f} for {market_hash_name}")
                                    return price
                                except ValueError:
                                    pass
                        else:
                            logger.debug(f"Steam API returned unsuccessful response for {market_hash_name}")
                            
            except asyncio.TimeoutError:
                logger.debug(f"Timeout getting Steam price for {market_hash_name}, attempt {attempt + 1}")
            except Exception as e:
                logger.debug(f"Failed to get Steam price for {market_hash_name} (attempt {attempt + 1}): {e}")
                
        return None
    
    def detect_price_outliers(self, prices_by_rarity: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """Detect price outliers using IQR method for each rarity group"""
        outliers_by_rarity = {}
        
        for rarity, prices in prices_by_rarity.items():
            valid_prices = [p for p in prices if p > 0]
            if len(valid_prices) < 4:
                continue
            
            q1 = statistics.quantiles(valid_prices, n=4)[0]  # 25th percentile
            q3 = statistics.quantiles(valid_prices, n=4)[2]  # 75th percentile
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [p for p in valid_prices if p < lower_bound or p > upper_bound]
            if outliers:
                outliers_by_rarity[rarity] = outliers
                logger.info(f"Detected {len(outliers)} price outliers for {rarity}: {outliers}")
        
        return outliers_by_rarity

    def is_price_reasonable(self, market_hash_name: str, price: float, rarity: str) -> bool:
        """Check if price is reasonable for the given rarity"""
        # Maximum reasonable prices by rarity (conservative estimates)
        max_prices = {
            'Consumer Grade': 3.0,     # Most consumer skins are under $3
            'Industrial Grade': 10.0,   # Most industrial skins are under $10
            'Mil-Spec Grade': 25.0,    # Most mil-spec skins are under $25
            'Restricted': 100.0,       # Most restricted skins are under $100
            'Classified': 300.0,       # Most classified skins are under $300
            'Covert': 1000.0           # Most covert skins are under $1000 (exceptions for rare patterns)
        }
          # Minimum reasonable prices
        min_price = 0.03  # Steam minimum
        max_price = max_prices.get(rarity, 50.0)  # Default to $50 for unknown rarities
        
        if price < min_price or price > max_price:
            logger.warning(f"Suspicious price for {market_hash_name} ({rarity}): ${price:.2f} (expected: ${min_price:.2f}-${max_price:.2f})")
            return False
        
        return True
        
    async def validate_and_correct_price(self, market_hash_name: str, price: float, rarity: str, tolerance_percent: float = 20.0) -> Optional[float]:
        """Validate price using Steam Market as authoritative source with strict tolerance"""
        # Add small delay to avoid rate limiting Steam API
        await asyncio.sleep(0.5)
        
        # Get Steam Market price as the authoritative source
        steam_price = await self.get_steam_market_price(market_hash_name)
        
        if steam_price is None:
            # If no Steam price available, reject the item entirely for safety
            logger.warning(f"No Steam price available for {market_hash_name}, excluding from analysis for safety")
            return None
        
        # Steam price is available - validate it first
        if not self.is_price_reasonable(market_hash_name, steam_price, rarity):
            logger.warning(f"Steam price ${steam_price:.2f} failed sanity check for {market_hash_name}")
            return None
        
        # Calculate the difference between external price and Steam price
        if steam_price > 0:
            price_difference_percent = abs(price - steam_price) / steam_price * 100
            
            if price_difference_percent <= tolerance_percent:
                # Use Steam price as the authoritative source
                logger.info(f"Using Steam price ${steam_price:.2f} for {market_hash_name} (external: ${price:.2f}, diff: {price_difference_percent:.1f}%)")
                return steam_price
            else:
                # Price difference is too large, exclude this item
                logger.warning(f"Large price discrepancy for {market_hash_name}: Steam ${steam_price:.2f} vs external ${price:.2f} ({price_difference_percent:.1f}% diff), excluding")
                return None
        
        # Use Steam price as authoritative
        return steam_price
