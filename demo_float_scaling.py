import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

def demonstrate_float_scaling():
    """Demonstrate how float scaling works with different skins"""
    
    finder = ComprehensiveTradeUpFinder()
    
    print("🎯 CS2 Trade-up Float Scaling Demonstration")
    print("=" * 60)
    
    # Different output skins with varying float ranges
    test_skins = [
        {
            'name': 'AK-47 | Redline',
            'min_float': 0.15,  # FT-BS only
            'max_float': 1.0
        },
        {
            'name': 'M4A4 | Asiimov', 
            'min_float': 0.18,  # FT-BS only
            'max_float': 1.0
        },
        {
            'name': 'AWP | Lightning Strike',
            'min_float': 0.0,   # All conditions
            'max_float': 0.08
        }
    ]
    
    # Test inputs representing different wear conditions
    test_inputs = [
        (0.035, "Factory New"),
        (0.11, "Minimal Wear"), 
        (0.265, "Field-Tested"),
        (0.415, "Well-Worn"),
        (0.725, "Battle-Scarred")
    ]
    
    for skin in test_skins:
        print(f"\n🔫 {skin['name']}")
        print(f"   Float Range: {skin['min_float']} - {skin['max_float']}")
        print(f"   Input Condition → Scaled Output (Float)")
        print("   " + "-" * 45)
        
        for input_float, input_condition in test_inputs:
            scaled_float, predicted_condition = finder._calculate_output_float_and_condition(
                input_float, skin
            )
            
            print(f"   {input_condition:13} → {predicted_condition:13} ({scaled_float:.6f})")
    
    print(f"\n📈 Key Insights:")
    print(f"   • Input floats are scaled to each output skin's specific range")
    print(f"   • Same input can produce different output conditions for different skins")
    print(f"   • Skins with narrow ranges (like AWP Lightning Strike) have predictable outputs")
    print(f"   • Skins with wide ranges show more variation in output conditions")

if __name__ == "__main__":
    demonstrate_float_scaling()
