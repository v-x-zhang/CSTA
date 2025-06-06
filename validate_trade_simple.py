"""
Simple Trade-up Validation without CSFloat API
Shows trade-up details with price validation from comprehensive database
"""

import asyncio
import sys
import os
sys.path.append('src')

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def main():
    print('🔄 Initializing CS2 Trade-up Validator...')
    
    # Initialize components
    try:
        finder = ComprehensiveTradeUpFinder()
        await finder.initialize()
        print('✅ Components initialized successfully')
        print(f'   Loaded {len(finder._cached_prices)} prices from cache')
    except Exception as e:
        print(f'❌ Failed to initialize components: {e}')
        return
    
    # Get the first profitable trade-up
    print('\n🔍 Searching for profitable trades...')
    try:
        profitable_trades = await finder.find_profitable_trades(min_profit=1.0, limit=1)
        
        if not profitable_trades:
            print('❌ No profitable trades found')
            return
            
        first_trade = profitable_trades[0]
        print(f'✅ Found profitable trade')
        print(f'   Total cost: ${first_trade.input_config.total_cost:.2f}')
        print(f'   Expected profit: ${first_trade.expected_profit:.2f}')
        print(f'   ROI: {first_trade.roi_percentage:.1f}%')
        
    except Exception as e:
        print(f'❌ Error finding trades: {e}')
        return
    
    # Show detailed trade analysis
    print('\n' + '='*80)
    print('                     TRADE-UP VALIDATION REPORT')
    print('='*80)
    
    # Input analysis
    print('\n📋 INPUT REQUIREMENTS:')
    print('-' * 50)
    
    # Group skins by type for display
    skin_counts = {}
    total_cost = 0
    
    for skin in first_trade.input_config.skins:
        if skin.name in skin_counts:
            skin_counts[skin.name]['count'] += 1
        else:
            skin_counts[skin.name] = {
                'count': 1,
                'price': float(skin.price),
                'collection': skin.collection,
                'rarity': skin.rarity,
                'float_range': f"{skin.float_min:.3f} - {skin.float_max:.3f}"
            }
    
    for name, info in skin_counts.items():
        item_total = info['count'] * info['price']
        total_cost += item_total
        
        print(f"🔧 {info['count']}x {name}")
        print(f"   Collection: {info['collection']}")
        print(f"   Rarity: {info['rarity']}")
        print(f"   Price: ${info['price']:.2f} each = ${item_total:.2f} total")
        print(f"   Float Range: {info['float_range']}")
          # Check price validation status
        skin_data = finder.db_manager.get_skin_by_name(name)
        if skin_data:
            validation_status = finder.db_manager.get_price_validation_status(name)
            if validation_status:
                status = validation_status.get('status', 'unvalidated')
                if status == 'valid':
                    print(f"   ✅ Price validated")
                elif status == 'invalid':
                    discrepancy = validation_status.get('discrepancy_percent')
                    if discrepancy is not None:
                        print(f"   ⚠️  Price validation: {discrepancy:.1f}% discrepancy detected")
                    else:
                        print(f"   ⚠️  Price validation: Invalid (excluded from analysis)")
                else:
                    print(f"   ⏳ Price validation: {status}")
            else:
                print(f"   ❓ Price validation: Not checked")
        print()
    
    print(f"💰 TOTAL INVESTMENT: ${total_cost:.2f}")
    print(f"📊 AVERAGE INPUT FLOAT: {first_trade.input_config.average_float:.6f}")
    
    # Output analysis
    print('\n🎯 POSSIBLE OUTPUTS:')
    print('-' * 50)
    
    expected_value = 0
    profitable_outcomes = 0
    break_even_outcomes = 0
    losing_outcomes = 0
    
    for output in first_trade.output_skins:
        profit = float(output.skin.price) - total_cost
        expected_value += float(output.expected_value)
        
        if profit > 0:
            profitable_outcomes += 1
            status_icon = "✅"
            status = f"Profit: ${profit:.2f}"
        elif profit == 0:
            break_even_outcomes += 1
            status_icon = "⚖️"
            status = "Break-even"
        else:
            losing_outcomes += 1
            status_icon = "❌"
            status = f"Loss: ${abs(profit):.2f}"
        
        print(f"{status_icon} {output.skin.name}")
        print(f"   Collection: {output.skin.collection}")
        print(f"   Value: ${output.skin.price:.2f}")
        print(f"   Probability: {output.probability:.1%}")
        print(f"   Expected Value: ${output.expected_value:.2f}")
        print(f"   {status}")
        print(f"   Float Range: {output.skin.float_min:.3f} - {output.skin.float_max:.3f}")
        print()
    
    # Financial summary
    print('\n💵 FINANCIAL ANALYSIS:')
    print('-' * 50)
    print(f"Total Investment: ${total_cost:.2f}")
    print(f"Expected Return: ${expected_value:.2f}")
    print(f"Expected Profit: ${first_trade.expected_profit:.2f}")
    print(f"ROI: {first_trade.roi_percentage:.1f}%")
    print(f"Market Fee (15%): Already deducted from expected return")
    
    # Outcome statistics
    print('\n📊 OUTCOME STATISTICS:')
    print('-' * 50)
    total_outcomes = len(first_trade.output_skins)
    print(f"Total possible outcomes: {total_outcomes}")
    print(f"Profitable outcomes: {profitable_outcomes} ({profitable_outcomes/total_outcomes:.1%})")
    print(f"Break-even outcomes: {break_even_outcomes} ({break_even_outcomes/total_outcomes:.1%})")
    print(f"Losing outcomes: {losing_outcomes} ({losing_outcomes/total_outcomes:.1%})")
    
    # Risk assessment
    print('\n⚠️  RISK ASSESSMENT:')
    print('-' * 50)
    if first_trade.guaranteed_profit:
        print("✅ GUARANTEED PROFIT - All outcomes are profitable!")
    else:
        loss_probability = losing_outcomes / total_outcomes
        if loss_probability > 0.5:
            print(f"🔴 HIGH RISK - {loss_probability:.1%} chance of loss")
        elif loss_probability > 0.3:
            print(f"🟡 MEDIUM RISK - {loss_probability:.1%} chance of loss")
        else:
            print(f"🟢 LOW RISK - {loss_probability:.1%} chance of loss")
    
    # Execution instructions
    print('\n🎯 EXECUTION STEPS:')
    print('-' * 50)
    print("1. Purchase the required input skins from Steam Market:")
    for name, info in skin_counts.items():
        print(f"   • Buy {info['count']}x {name} at ~${info['price']:.2f} each")
    print()
    print("2. Ensure all items are in your CS2 inventory")
    print("3. Open CS2 and navigate to the Trade-up Contract")
    print("4. Add the 10 items to the contract")
    print("5. Execute the trade-up")
    print("6. Sell the resulting item on Steam Market")
    print()
    print("💡 TIP: Consider the market volatility and ensure prices haven't changed significantly before executing!")
    
    print('\n' + '='*80)
    print('                     VALIDATION COMPLETE')
    print('='*80)
    
    # Close resources
    await finder.close()

if __name__ == '__main__':
    asyncio.run(main())
