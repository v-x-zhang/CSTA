"""
Result formatting utilities for trade-up calculations.
Provides human-readable output of trade-up opportunities.
"""

import logging
from typing import List
from decimal import Decimal

from .models import TradeUpResult, OutputSkin, Skin

logger = logging.getLogger(__name__)

class TradeUpFormatter:
    """Formats trade-up results for display"""
    
    @staticmethod
    def format_currency(amount: Decimal) -> str:
        """Format decimal amount as currency"""
        return f"${amount:.2f}"
    
    @staticmethod
    def format_percentage(decimal_value: Decimal) -> str:
        """Format decimal as percentage"""
        return f"{(decimal_value * 100):.1f}%"
    
    @staticmethod
    def format_single_result(result: TradeUpResult, rank: int = 1) -> str:
        """Format a single trade-up result"""
        lines = []
        
        # Header
        lines.append(f"=== TRADE-UP OPPORTUNITY #{rank} ===")
        lines.append("")
          # Investment summary
        lines.append("📊 INVESTMENT SUMMARY:")
        lines.append(f"   Total Cost: {TradeUpFormatter.format_currency(result.input_config.total_cost)}")
        lines.append(f"   Expected Value: {TradeUpFormatter.format_currency(result.expected_output_price)}")
        lines.append(f"   Expected Profit: {TradeUpFormatter.format_currency(result.raw_profit)}")
        lines.append(f"   ROI: {TradeUpFormatter.format_percentage(result.roi_percentage / 100.0)}")
        
        if result.guaranteed_profit:
            lines.append(f"   ✅ GUARANTEED PROFIT: {TradeUpFormatter.format_currency(result.profit_margin)}")
        
        lines.append("")
          # Input skins
        lines.append("🔧 REQUIRED INPUT SKINS (10 total):")
        input_summary = {}
        for skin in result.input_config.skins:
            key = f"{skin.name} ({skin.collection})"
            if key not in input_summary:
                input_summary[key] = {'count': 0, 'price': skin.price}
            input_summary[key]['count'] += 1
        
        for skin_info, data in input_summary.items():
            count = data['count']
            price = data['price']
            total_price = price * count
            lines.append(f"   {count}x {skin_info}")
            lines.append(f"      @ {TradeUpFormatter.format_currency(price)} each = {TradeUpFormatter.format_currency(total_price)}")
        
        lines.append("")
          # Float Analysis
        lines.append("🎲 FLOAT ANALYSIS:")
        lines.append(f"   Input Float (category midpoint): {result.input_config.average_float:.6f}")
        
        # Determine condition from float
        avg_float = result.input_config.average_float
        if avg_float < 0.07:
            condition = "Factory New"
        elif avg_float < 0.15:
            condition = "Minimal Wear"
        elif avg_float < 0.38:
            condition = "Field-Tested"
        elif avg_float < 0.45:
            condition = "Well-Worn"
        else:
            condition = "Battle-Scarred"
            
        lines.append(f"   Input Condition: {condition}")
        lines.append("   ⚡ Output float scaling: Each skin will have different predicted conditions!")
        lines.append("")
        
        # Possible outputs with scaled conditions
        lines.append("🎯 POSSIBLE OUTCOMES:")
        
        # Sort outputs by value (highest first)
        sorted_outputs = sorted(result.output_skins, key=lambda o: o.skin.price, reverse=True)
        
        for output in sorted_outputs:
            profit = output.skin.price - result.input_config.total_cost
            profit_indicator = "✅" if profit > 0 else "❌" if profit < 0 else "⚖️"
            
            lines.append(f"   {profit_indicator} {output.skin.name} ({output.skin.collection})")
            lines.append(f"      Value: {TradeUpFormatter.format_currency(output.skin.price)}")
            lines.append(f"      Profit: {TradeUpFormatter.format_currency(profit)}")
            lines.append(f"      Probability: {TradeUpFormatter.format_percentage(output.probability)}")
            
            # Show scaled output condition if available
            if hasattr(output, 'predicted_condition') and hasattr(output, 'predicted_float'):
                lines.append(f"      Predicted Output: {output.predicted_float:.6f} ({output.predicted_condition})")
            else:
                lines.append(f"      Predicted Output: {output.skin.float_mid:.6f} (varies by skin's float range)")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_multiple_results(results: List[TradeUpResult], title: str = "TRADE-UP OPPORTUNITIES") -> str:
        """Format multiple trade-up results"""
        if not results:
            return "No profitable trade-up opportunities found."
        
        lines = []
        lines.append(f"{'='*50}")
        lines.append(f"{title.center(50)}")
        lines.append(f"{'='*50}")
        lines.append("")
        
        for i, result in enumerate(results, 1):
            lines.append(TradeUpFormatter.format_single_result(result, i))
            if i < len(results):
                lines.append("\n" + "─" * 80 + "\n")
        
        return "\n".join(lines)
    @staticmethod
    def format_summary_table(results: List[TradeUpResult]) -> str:
        """Format results as a summary table"""
        if not results:
            return "No results to display."
        
        lines = []
        lines.append("📈 TRADE-UP OPPORTUNITIES SUMMARY")
        lines.append("=" * 80)
        lines.append("")
        
        # Header
        header = f"{'#':<3} {'Expected Profit':<15} {'Guaranteed':<12} {'Cost':<10} {'Collections':<20}"
        lines.append(header)
        lines.append("-" * 80)
        
        # Results
        for i, result in enumerate(results, 1):
            expected_profit = result.raw_profit
            guaranteed = "YES" if result.guaranteed_profit else "NO"
            cost = TradeUpFormatter.format_currency(result.input_config.total_cost)
            
            # Get unique collections from inputs
            collections = set(skin.collection for skin in result.input_config.skins)
            collections_str = ", ".join(list(collections)[:2])  # Show first 2 collections
            if len(collections) > 2:
                collections_str += f" +{len(collections)-2}"
            
            row = f"{i:<3} {TradeUpFormatter.format_currency(expected_profit):<15} {guaranteed:<12} {cost:<10} {collections_str:<20}"
            lines.append(row)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_market_summary(summary: dict) -> str:
        """Format market data summary"""
        lines = []
        lines.append("📊 MARKET DATA SUMMARY")
        lines.append("=" * 40)
        lines.append(f"Total Collections: {summary.get('total_collections', 0)}")
        lines.append(f"Total Skins: {summary.get('total_skins', 0)}")
        lines.append("")
        lines.append("Skins by Rarity:")
        
        for rarity, count in summary.get('skins_by_rarity', {}).items():
            lines.append(f"  {rarity}: {count}")
        
        if 'last_updated' in summary:
            import time
            updated_time = time.ctime(summary['last_updated'])
            lines.append(f"\nLast Updated: {updated_time}")
        
        return "\n".join(lines)

def format_trade_up_result(result: TradeUpResult, rank: int = 1) -> str:
    """Convenience function to format a single result"""
    return TradeUpFormatter.format_single_result(result, rank)

def format_trade_up_results(results: List[TradeUpResult], title: str = "TRADE-UP OPPORTUNITIES") -> str:
    """Convenience function to format multiple results"""
    return TradeUpFormatter.format_multiple_results(results, title)

def format_results_table(results: List[TradeUpResult]) -> str:
    """Convenience function to format results as table"""
    return TradeUpFormatter.format_summary_table(results)
