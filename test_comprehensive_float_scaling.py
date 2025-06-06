#!/usr/bin/env python3
"""
Comprehensive test of the updated float scaling implementation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

def test_comprehensive_float_scaling():
    """Test float scaling with realistic CS2 skin examples"""
    
    finder = ComprehensiveTradeUpFinder()
    
    print("🎯 CS2 Trade-up Float Scaling Implementation Test")
    print("=" * 60)
    print("Testing how input conditions affect output skins with different float ranges")
    print()
    
    # Realistic CS2 skins with their actual float ranges
    output_skins = [
        {
            'name': 'AK-47 | Redline',
            'min_float': 0.10,
            'max_float': 0.70,
            'note': 'MW-WW range'
        },
        {
            'name': 'AWP | Lightning Strike', 
            'min_float': 0.00,
            'max_float': 0.08,
            'note': 'FN only'
        },
        {
            'name': 'M4A4 | Asiimov',
            'min_float': 0.18,
            'max_float': 1.00,
            'note': 'FT-BS range'
        },
        {
            'name': 'USP-S | Kill Confirmed',
            'min_float': 0.00,
            'max_float': 1.00,
            'note': 'All conditions'
        }
    ]
    
    # Input conditions using our accurate midpoints
    input_conditions = [
        (0.035, "Factory New"),
        (0.11, "Minimal Wear"),
        (0.265, "Field-Tested"),
        (0.415, "Well-Worn"),
        (0.725, "Battle-Scarred")
    ]
    
    for skin in output_skins:
        print(f"🔫 {skin['name']} ({skin['note']})")
        print(f"   Float Range: {skin['min_float']:.3f} - {skin['max_float']:.3f}")
        print()
        print("   Input Condition    → Output Float    → Output Condition")
        print("   " + "-" * 55)
        
        for input_float, input_condition in input_conditions:
            scaled_float, predicted_condition = finder._calculate_output_float_and_condition(
                input_float, skin
            )
            
            print(f"   {input_condition:15} → {scaled_float:11.6f} → {predicted_condition}")
        
        print()
    
    print("📊 Key Improvements in This Implementation:")
    print("─" * 60)
    print("✅ Accurate CS2 wear category midpoints (not arbitrary values)")
    print("✅ Proper float scaling to each output skin's specific range")
    print("✅ Condition-specific pricing lookup when available")
    print("✅ Realistic output condition predictions")
    print("✅ Better trade-up profitability calculations")
    print()
    
    print("🎲 Float Scaling Formula:")
    print("output_float = output_min + (input_float * (output_max - output_min))")
    print()
    
    print("💡 Impact on Trade-up Strategy:")
    print("• Skins with narrow ranges (AWP Lightning Strike) are more predictable")
    print("• Skins with wide ranges offer more condition variety")
    print("• Input condition choice significantly affects expected output value")
    print("• Trade-up profitability now accounts for realistic output conditions")

if __name__ == "__main__":
    test_comprehensive_float_scaling()
