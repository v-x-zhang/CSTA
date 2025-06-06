"""
API Client for Price Empire and CSFloat APIs
Handles all external API communications with rate limiting and error handling.
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging

from .config import config
from .models import Skin

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter for API requests"""
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        now = time.time()
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request) + 1
            logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
        
        self.requests.append(now)

class PriceEmpireClient:
    """Client for Price Empire API"""
    
    def __init__(self):
        self.base_url = config.api.PRICE_EMPIRE_BASE_URL        
        self.headers = config.price_empire_headers        
        self.rate_limiter = RateLimiter(config.api.PRICE_EMPIRE_RATE_LIMIT)
    
    async def fetch_all_skins(self, session: aiohttp.ClientSession, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all marketable skins from Price Empire API"""
        await self.rate_limiter.acquire()
        
        # Try the items endpoint first for full metadata, then fall back to prices
        endpoints_to_try = [
            {
                "name": "Items endpoint",
                "url": f"{self.base_url}/items",
                "params": {"app_id": 730}
            },
            {
                "name": "Prices endpoint",
                "url": f"{self.base_url}/items/prices",
                "params": {"app_id": 730, "currency": "USD"}
            }
        ]
        
        for endpoint in endpoints_to_try:
            try:
                logger.info(f"Trying Price Empire {endpoint['name']}")
                async with session.get(endpoint["url"], headers=self.headers, params=endpoint["params"]) as response:
                    logger.info(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        total_items = len(data)
                        logger.info(f"Successfully fetched {total_items} items from Price Empire ({endpoint['name']})")
                        
                        # Apply limit if specified
                        if limit and limit < total_items:
                            data = data[:limit]
                            logger.info(f"Limited to first {limit} items for testing")
                        
                        return data
                    elif response.status == 401:
                        logger.error("Price Empire API authentication failed")
                        return []
                    else:
                        error_text = await response.text()
                        logger.warning(f"{endpoint['name']} failed: {response.status}")
                        logger.debug(f"Error details: {error_text[:200]}")
                        
            except Exception as e:
                logger.error(f"Exception with {endpoint['name']}: {e}")
                continue
        
        logger.error("All Price Empire endpoints failed")
        return []
    
    async def fetch_item_details(self, session: aiohttp.ClientSession, item_name: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information about a specific item"""
        await self.rate_limiter.acquire()
        
        url = f"{self.base_url}/items/{item_name}"
        params = {"app_id": 730}
        
        try:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Could not fetch details for {item_name}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching item details for {item_name}: {e}")
            return None

    def _combine_items_and_prices(self, items_data: List[Dict], price_data: List[Dict]) -> List[Dict[str, Any]]:
        """Combine items metadata with pricing data"""
        # Create a lookup dictionary for prices by market_hash_name
        price_lookup = {}
        for item in price_data:
            market_hash_name = item.get('market_hash_name')
            if market_hash_name and item.get('prices'):
                # Get the best Steam price
                steam_prices = [p for p in item['prices'] if p.get('provider_key') == 'steam']
                if steam_prices:
                    price_lookup[market_hash_name] = steam_prices[0]
        
        # Combine items with pricing
        combined_data = []
        for item in items_data:
            market_hash_name = item.get('market_hash_name')
            if market_hash_name:
                # Add pricing data if available
                if market_hash_name in price_lookup:
                    item['price_data'] = price_lookup[market_hash_name]
                combined_data.append(item)
        
        return combined_data

class CSFloatClient:
    """Client for CSFloat API"""
    
    def __init__(self):
        self.base_url = config.api.CSFLOAT_BASE_URL        
        self.headers = config.csfloat_headers
        self.rate_limiter = RateLimiter(config.api.CSFLOAT_RATE_LIMIT)
    
    async def fetch_market_data(self, session: aiohttp.ClientSession, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch market data from CSFloat listings"""
        all_listings = []
        page = 0
        
        while len(all_listings) < limit:
            await self.rate_limiter.acquire()
            
            url = f"{self.base_url}/listings"
            params = {
                "page": page,
                "limit": min(50, limit - len(all_listings)),  # CSFloat max is 50 per page
                "sort_by": "most_recent",
                "type": "buy_now"  # Focus on buy_now listings for price data
            }
            
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data:  # No more data
                            break
                        all_listings.extend(data)
                        page += 1
                        logger.info(f"Fetched page {page}, total listings: {len(all_listings)}")
                    else:
                        logger.error(f"CSFloat API error: {response.status}")
                        break
            except Exception as e:
                logger.error(f"Error fetching CSFloat data: {e}")
                break
        
        return all_listings

class APIClient:
    """Main API client that coordinates both Price Empire and CSFloat"""
    
    def __init__(self, use_mock_data: bool = False, use_profitable_mock: bool = False, limit_items: Optional[int] = None, use_csfloat: bool = False):
        self.price_empire = PriceEmpireClient()
        self.csfloat = CSFloatClient() if use_csfloat else None
        self.use_mock_data = use_mock_data
        self.use_profitable_mock = use_profitable_mock
        self.limit_items = limit_items
        self.use_csfloat = use_csfloat
        
    async def fetch_all_market_data(self) -> List[Skin]:
        """Fetch all skin data from both APIs and combine"""
        logger.debug(f"APIClient: use_mock_data={self.use_mock_data}, use_profitable_mock={self.use_profitable_mock}")
        
        if self.use_mock_data:
            if self.use_profitable_mock:
                logger.info("Using profitable mock data for demonstration")
                # Lazy import to avoid circular dependency
                from .mock_data_profitable import generate_profitable_mock_skins
                return generate_profitable_mock_skins()
            else:
                logger.info("Using realistic mock data for testing")
                # Lazy import to avoid circular dependency
                from .mock_data import generate_mock_skins
                return generate_mock_skins()
        logger.info("Starting to fetch market data from APIs")
        
        async with aiohttp.ClientSession() as session:
            # Fetch comprehensive skin data from Price Empire
            price_empire_data = await self.price_empire.fetch_all_skins(session, limit=self.limit_items)
            logger.info(f"Fetched {len(price_empire_data)} items from Price Empire")
            
            # Only fetch minimal CSFloat data if enabled and needed
            csfloat_data = []
            if self.use_csfloat and self.csfloat:
                # Use very small limit to minimize rate limiting
                small_limit = min(50, len(price_empire_data) // 4) if price_empire_data else 50
                logger.info(f"Fetching minimal CSFloat data (limit: {small_limit}) to avoid rate limiting")
                csfloat_data = await self.csfloat.fetch_market_data(session, limit=small_limit)
                logger.info(f"Fetched {len(csfloat_data)} listings from CSFloat")
            else:
                logger.info("Skipping CSFloat API to avoid rate limiting - using Price Empire data only")
            
            # Combine data into Skin objects
            if csfloat_data:
                skins = self._create_skins_from_combined_data(price_empire_data, csfloat_data)
            else:
                skins = self._create_skins_from_price_empire_only(price_empire_data)
            
            logger.info(f"Created {len(skins)} valid trade-up skins")
            return skins
    
    def _create_skins_from_combined_data(self, price_empire_data: List[Dict], csfloat_data: List[Dict]) -> List[Skin]:
        """Create Skin objects from combined API data"""
        skins = []
        
        # Create lookup for CSFloat data by market_hash_name
        csfloat_lookup = {}
        for listing in csfloat_data:
            item = listing.get('item', {})
            market_hash_name = item.get('market_hash_name')
            if market_hash_name:
                if market_hash_name not in csfloat_lookup:
                    csfloat_lookup[market_hash_name] = []
                csfloat_lookup[market_hash_name].append({
                    'price': listing.get('price', 0) / 100,  # Convert from cents to dollars
                    'float': item.get('float_value'),
                    'collection': item.get('collection'),
                    'rarity': item.get('rarity'),
                    'stattrak': item.get('is_stattrak', False),
                    'souvenir': item.get('is_souvenir', False)
                })
          # Process Price Empire data
        for item in price_empire_data:
            try:
                skin = self._create_skin_from_price_empire_data(item, csfloat_lookup)
                if skin and self._is_valid_tradeup_skin(skin):
                    skins.append(skin)
            except Exception as e:
                logger.error(f"Error creating skin from data: {e}")
                continue
        
        return skins
      
    def _is_valid_tradeup_skin(self, skin: Skin) -> bool:
        """Check if skin is valid for trade-up calculations"""
        return (
            skin.marketable and
            not skin.stattrak and
            skin.rarity in config.trade_up.RARITIES and
            skin.price > 0 and
            skin.collection != 'Unknown'
        )
    
    def _create_skin_from_price_empire_data(self, item_data: Dict[str, Any], csfloat_lookup: Dict) -> Optional[Skin]:
        """Create a Skin object from Price Empire data enhanced with CSFloat data"""
        try:
            market_hash_name = item_data.get('market_hash_name', '')
            if not market_hash_name:
                return None
            
            # Extract basic item info
            name = market_hash_name
            weapon_name = item_data.get('weapon', {}).get('name', '')
            pattern = item_data.get('pattern', '')
            wear = item_data.get('wear', '')
            
            # Build full name if needed
            if weapon_name and pattern and wear:
                name = f"{weapon_name} | {pattern} ({wear})"
            
            # Get collection info
            collections = item_data.get('collections', [])
            collection = collections[0].get('name', 'Unknown') if collections else 'Unknown'
            
            # Map rarity from Price Empire format
            rarity_info = item_data.get('rarity', {})
            rarity_name = rarity_info.get('name', 'Unknown')
            rarity_map = {
                'Consumer Grade': 'Consumer',
                'Industrial Grade': 'Industrial', 
                'Mil-Spec Grade': 'Mil-Spec',
                'Restricted': 'Restricted',
                'Classified': 'Classified',
                'Covert': 'Covert',
                'Contraband': 'Contraband'
            }
            rarity = rarity_map.get(rarity_name, rarity_name)
            
            # Get price from Price Empire or CSFloat
            price = Decimal('0')
            price_data = item_data.get('price_data')
            if price_data and price_data.get('price'):
                price = Decimal(str(price_data['price']))
            elif market_hash_name in csfloat_lookup:
                # Use average price from CSFloat listings
                csfloat_items = csfloat_lookup[market_hash_name]
                prices = [item['price'] for item in csfloat_items if item['price'] > 0]
                if prices:
                    price = Decimal(str(sum(prices) / len(prices)))
            
            # Get float range
            min_float = item_data.get('min_float', 0.0)
            max_float = item_data.get('max_float', 1.0)
            
            # Check if it's StatTrak or Souvenir
            stattrak = item_data.get('stattrak', False) or 'StatTrak' in name
            souvenir = item_data.get('souvenir', False) or 'Souvenir' in name
            
            return Skin(
                name=name,
                collection=collection,
                rarity=rarity,
                price=price,
                float_min=min_float,
                float_max=max_float,
                marketable=True,
                stattrak=stattrak
            )
        
        except Exception as e:
            logger.error(f"Error creating skin from Price Empire data: {e}")
            return None
    
    def _create_skins_from_price_empire_only(self, price_empire_data: List[Dict]) -> List[Skin]:
        """Create Skin objects from Price Empire data only"""
        skins = []
        
        for item in price_empire_data:
            try:
                skin = self._create_skin_from_price_empire_data_only(item)
                if skin and self._is_valid_tradeup_skin(skin):
                    skins.append(skin)
            except Exception as e:
                logger.error(f"Error creating skin from data: {e}")                
                continue
        
        return skins

    def _create_skin_from_price_empire_data_only(self, item_data: Dict[str, Any]) -> Optional[Skin]:
        """Create a Skin object from Price Empire data only"""
        try:
            # Get market hash name first
            market_hash_name = item_data.get('market_hash_name', '')
            if not market_hash_name:
                logger.debug(f"No market_hash_name found in item: {item_data}")
                return None
                
            # Debug: Log the first few items to understand data structure
            if not hasattr(self, '_debug_logged_sample'):
                logger.info(f"DEBUG: Sample Price Empire item data structure:")
                logger.info(f"Keys: {list(item_data.keys())}")
                logger.info(f"Sample data: {str(item_data)[:500]}...")
                self._debug_logged_sample = True
                
            # Debug: Log which skins we're processing (with unicode-safe logging)
            if not hasattr(self, '_debug_skin_count'):
                self._debug_skin_count = 0
            self._debug_skin_count += 1
            if self._debug_skin_count <= 10:
                try:
                    logger.info(f"Processing skin {self._debug_skin_count}: {market_hash_name}")
                except UnicodeEncodeError:
                    logger.info(f"Processing skin {self._debug_skin_count}: {market_hash_name.encode('ascii', 'replace').decode('ascii')}")
            
            # Parse name components from market_hash_name
            # Format is usually: "Weapon | Skin (Condition)" or "Weapon | Skin"
            name = market_hash_name
            weapon_name = ""
            pattern = ""
            wear = ""
            
            # Try to parse market_hash_name for weapon and skin info
            if " | " in market_hash_name:
                parts = market_hash_name.split(" | ", 1)
                weapon_name = parts[0]
                skin_part = parts[1]
                
                # Check if condition is in parentheses
                if "(" in skin_part and skin_part.endswith(")"):
                    pattern = skin_part[:skin_part.rfind("(")].strip()
                    wear = skin_part[skin_part.rfind("(")+1:-1]                
                else:
                    pattern = skin_part
            
            # Use skin mapping to get collection and rarity
            from .skin_mapping import SkinMapper            
            mapper = SkinMapper()
            collection, rarity = mapper.get_skin_info(market_hash_name)
            
            if not collection or not rarity:
                try:
                    logger.debug(f"No collection/rarity mapping found for: {market_hash_name}")
                except UnicodeEncodeError:
                    logger.debug(f"No collection/rarity mapping found for: {market_hash_name.encode('ascii', 'replace').decode('ascii')}")
                return None
            
            logger.debug(f"Successfully mapped {market_hash_name} -> {collection}/{rarity}")
            
            # Get price from Price Empire prices array
            price = Decimal('0')
            prices = item_data.get('prices', [])
            if prices and isinstance(prices, list):
                # Look for Steam price first, then any price
                steam_price = None
                any_price = None
                
                for price_entry in prices:
                    if price_entry.get('provider_key') == 'steam':
                        steam_price = price_entry.get('price')
                    if not any_price and price_entry.get('price'):
                        any_price = price_entry.get('price')
                
                # Use Steam price if available, otherwise any price
                price_value = steam_price or any_price
                if price_value:
                    # Price Empire prices appear to be in cents, convert to dollars
                    price = Decimal(str(price_value / 100))
            
            if price <= 0:
                logger.debug(f"No valid price found for {market_hash_name}")
                return None
            
            # Default float ranges by wear condition
            wear_float_ranges = {
                'Factory New': (0.00, 0.07),
                'Minimal Wear': (0.07, 0.15),
                'Field-Tested': (0.15, 0.38),
                'Well-Worn': (0.38, 0.45),
                'Battle-Scarred': (0.45, 1.00)
            }            
            
            min_float, max_float = wear_float_ranges.get(wear, (0.0, 1.0))
            
            # Check if it's StatTrak or Souvenir
            stattrak = 'StatTrak' in name
            
            return Skin(
                name=name,
                collection=collection,
                rarity=rarity,
                price=price,
                float_min=min_float,
                float_max=max_float,
                marketable=True,
                stattrak=stattrak
            )
        
        except Exception as e:
            logger.error(f"Error creating skin from Price Empire data: {e}")
            logger.debug(f"Item data: {item_data}")
            return None

    async def close(self) -> None:
        """Clean up resources"""
        # No persistent connections to close in this implementation
        pass