# CS2 Trade-up Calculator

A comprehensive CS2 trade-up calculator that finds profitable trade-up opportunities by analyzing market data from multiple APIs and applying CS2's exact trade-up mechanics.

## Features

- **Real-time Market Data**: Fetches skin prices from Price Empire API and float ranges from CSFloat API
- **Smart Caching**: Local SQLite database caches data to minimize API calls
- **Exact CS2 Mechanics**: Implements the precise probability formula `k_C / sum_over_collections`
- **Profit Analysis**: Finds both guaranteed profit and positive expected value trade-ups
- **Collection-Based**: Organizes skins by collection and rarity for accurate calculations
- **Rate Limited**: Respects API rate limits with intelligent request management

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd CSTA
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. **Set up your API keys** (see [SECURITY.md](SECURITY.md) for details):
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

4. Run the calculator:
```bash
python main.py
```

### Basic Usage

```python
import asyncio
from src import find_best_trades, format_trade_up_results

async def main():
    # Find profitable trade-ups with at least $2 profit
    results = await find_best_trades(min_profit=2.0, limit=5)
    
    if results:
        print(format_trade_up_results(results))
    else:
        print("No profitable opportunities found")

asyncio.run(main())
```

## Command Line Interface

The main application supports various command-line options:

```bash
# Basic usage - find profitable trades
python main.py

# Find guaranteed profit trades only
python main.py --guaranteed-only

# Set minimum profit threshold
python main.py --min-profit 5.0

# Limit input skin price
python main.py --max-price 20.0

# Focus on specific collections
python main.py --collections "The Dust 2 Collection" "The Mirage Collection"

# Show results in table format
python main.py --table

# Force refresh market data
python main.py --refresh

# Show market data summary
python main.py --summary
```

### Available Options

- `--min-profit FLOAT`: Minimum profit threshold in dollars (default: 1.0)
- `--max-price FLOAT`: Maximum input skin price in dollars  
- `--collections LIST`: Target collections to focus on
- `--guaranteed-only`: Show only guaranteed profit trades
- `--limit INT`: Maximum number of results (default: 10)
- `--refresh`: Force refresh of market data
- `--summary`: Show market data summary
- `--table`: Show results in table format
- `--log-level LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)

### Comprehensive Version (main_comprehensive.py)

The comprehensive version uses a complete skin database with runtime pricing:

```bash
# Use Steam Market pricing (recommended for accuracy)
python main_comprehensive.py --use-steam-pricing --all-prices

# Use external API pricing with Steam validation
python main_comprehensive.py --all-prices

# Use sample pricing (faster initialization, fewer opportunities)
python main_comprehensive.py --sample-size 2000

# Compare results with different pricing modes
python main_comprehensive.py --use-steam-pricing --min-profit 1.0
```

**Comprehensive Options:**
- `--use-steam-pricing`: Use Steam Market pricing database (more accurate economics)
- `--all-prices`: Load ALL available pricing data (recommended for best results)
- `--sample-size INT`: Number of prices to load if not using --all-prices (default: 2000)

**Steam Pricing Setup:**
```bash
# Build Steam pricing database (required for --use-steam-pricing)
python build_steam_pricing_database.py

# Check Steam pricing database statistics
python build_steam_pricing_database.py --stats-only
```

## How It Works

### Trade-up Mechanics

The calculator implements CS2's exact trade-up mechanics:

1. **Input Requirements**: Exactly 10 skins of the same rarity
2. **Output Rarity**: One tier higher than input rarity
3. **Probability Formula**: `P(skin) = (1/k_C) × (k_C/total_weight) = 1/total_weight`
   - Where `k_C` is the number of skins in collection C at the output rarity
   - `total_weight` is the sum of all k_C values for input collections

### Data Sources

- **Price Empire API**: Provides current market prices and collection information
- **CSFloat API**: Supplies float ranges for accurate skin data
- **Local Cache**: SQLite database stores data locally to reduce API calls

### Calculation Process

1. **Data Fetching**: Retrieve skin data from APIs with rate limiting
2. **Organization**: Group skins by collection and rarity
3. **Combination Generation**: Create viable input combinations (10 skins, same rarity)
4. **Probability Calculation**: Apply CS2's probability formula
5. **Profit Analysis**: Calculate expected value, min/max profits, and guaranteed profits
6. **Result Ranking**: Sort by profitability (guaranteed profit first, then expected value)

## API Configuration

The system requires API keys for data fetching. These are securely configured using environment variables:

1. Copy `.env.example` to `.env`
2. Add your actual API keys to the `.env` file
3. The keys are automatically loaded from environment variables

See [SECURITY.md](SECURITY.md) for detailed setup instructions.

Rate limits are automatically managed:
- Price Empire: 60 requests per minute
- CSFloat: 30 requests per minute

## Examples

### Simple Example

```python
from src import create_finder, format_results_table

async def find_trades():
    finder = await create_finder()
    
    # Find trades with at least $1 profit
    results = await finder.find_profitable_trades(min_profit=1.0)
    
    print(format_results_table(results))
    await finder.close()
```

### Advanced Example

```python
from src import TradeUpFinder, format_trade_up_result

async def advanced_example():
    finder = TradeUpFinder()
    await finder.initialize()
    
    # Find guaranteed profit trades
    guaranteed = await finder.find_guaranteed_profit_trades(
        max_input_price=15.0,
        limit=5
    )
    
    for i, result in enumerate(guaranteed, 1):
        print(format_trade_up_result(result, rank=i))
    
    await finder.close()
```

## Architecture

### Core Modules

- **`models.py`**: Data models for skins, trade-ups, and results
- **`config.py`**: Configuration settings and API keys
- **`api_client.py`**: API clients with rate limiting
- **`database.py`**: SQLite caching system
- **`calculator.py`**: Trade-up calculation engine
- **`trade_up_finder.py`**: Main orchestrator
- **`formatter.py`**: Result formatting utilities

### Data Flow

```
APIs → API Client → Database Cache → Calculator → Formatter → Output
```

## Rarity Mappings

The system supports these trade-up paths:

- Consumer Grade → Industrial Grade
- Industrial Grade → Mil-Spec  
- Mil-Spec → Restricted
- Restricted → Classified
- Classified → Covert

## Output Format

### Detailed Results

Each trade-up opportunity shows:
- Investment summary (cost, expected value, profit range)
- Required input skins with quantities and prices
- Possible outcomes with probabilities and profit potential
- Guaranteed profit indicator (if applicable)

### Table Format

Compact summary showing:
- Rank and expected profit
- Guaranteed profit status
- Total investment cost
- Collections involved

## Performance

- **Data Caching**: Reduces API calls and improves response time
- **Rate Limiting**: Prevents API throttling
- **Efficient Algorithms**: Optimized combination generation
- **Memory Management**: Handles large datasets efficiently

## Troubleshooting

### Common Issues

1. **No results found**: Try lowering profit thresholds or refreshing data
2. **API errors**: Check internet connection and API key validity
3. **Rate limiting**: The system handles this automatically
4. **Database issues**: Delete `data/trade_up_cache.db` to reset

### Logging

Enable debug logging for detailed information:
```bash
python main.py --log-level DEBUG
```

Logs are saved to `logs/trade_up_calculator.log` with automatic rotation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]

## Disclaimer

This tool is for educational and informational purposes only. Market prices are volatile and past performance doesn't guarantee future results. Always verify calculations and market conditions before making trades.