"""
Reset Price Validation Script
Resets all price validation parameters in the database to allow fresh validation with new market data.
"""

import sqlite3
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.logging_config import setup_logging

def reset_price_validation(db_path: str = 'data/comprehensive_skins.db'):
    """Reset all price validation parameters in the database"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Resetting price validation parameters...")
        
        # Check if price validation columns exist
        cursor.execute("PRAGMA table_info(comprehensive_skins)")
        columns = [row[1] for row in cursor.fetchall()]
        
        validation_columns = [
            'price_validation_status',
            'price_discrepancy_percent', 
            'last_price_check',
            'steam_price',
            'last_steam_check'
        ]
        
        existing_validation_columns = [col for col in validation_columns if col in columns]
        
        if not existing_validation_columns:
            print("ℹ️  No price validation columns found in database - nothing to reset")
            return
        
        print(f"📊 Found validation columns: {', '.join(existing_validation_columns)}")
        
        # Get count of records before reset
        cursor.execute("SELECT COUNT(*) FROM comprehensive_skins")
        total_records = cursor.fetchone()[0]
        
        # Count validated records before reset
        validated_count = 0
        if 'price_validation_status' in columns:
            cursor.execute("SELECT COUNT(*) FROM comprehensive_skins WHERE price_validation_status IS NOT NULL AND price_validation_status != 'unvalidated'")
            validated_count = cursor.fetchone()[0]
        
        print(f"📈 Total skins in database: {total_records:,}")
        print(f"🔍 Previously validated skins: {validated_count:,}")
        
        # Reset all validation fields to NULL (except set status to 'unvalidated')
        reset_queries = []
        
        if 'price_validation_status' in columns:
            reset_queries.append("price_validation_status = 'unvalidated'")
            
        if 'price_discrepancy_percent' in columns:
            reset_queries.append("price_discrepancy_percent = NULL")
            
        if 'last_price_check' in columns:
            reset_queries.append("last_price_check = NULL")
            
        if 'steam_price' in columns:
            reset_queries.append("steam_price = NULL")
            
        if 'last_steam_check' in columns:
            reset_queries.append("last_steam_check = NULL")
        
        if reset_queries:
            update_query = f"UPDATE comprehensive_skins SET {', '.join(reset_queries)}"
            cursor.execute(update_query)
            
            affected_rows = cursor.rowcount
            conn.commit()
            
            print(f"✅ Reset complete!")
            print(f"   🔄 Updated {affected_rows:,} records")
            print(f"   📝 All validation statuses set to 'unvalidated'")
            print(f"   🧹 Cleared cached Steam prices and validation timestamps")
            print()
            print("💡 Benefits of resetting:")
            print("   • Fresh price validation with current market data")
            print("   • Re-evaluation of previously excluded skins") 
            print("   • More accurate trade-up analysis")
            print("   • Removal of stale validation data")
            
        else:
            print("⚠️  No validation fields to reset")
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

def show_validation_summary(db_path: str = 'data/comprehensive_skins.db'):
    """Show summary of current validation status"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 PRICE VALIDATION SUMMARY")
        print("=" * 50)
        
        # Check if validation columns exist
        cursor.execute("PRAGMA table_info(comprehensive_skins)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'price_validation_status' not in columns:
            print("ℹ️  No price validation tracking in database")
            return
            
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM comprehensive_skins")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comprehensive_skins WHERE current_price IS NOT NULL AND current_price > 0")
        with_prices = cursor.fetchone()[0]
        
        print(f"Total skins: {total:,}")
        print(f"Skins with prices: {with_prices:,}")
        
        # Validation status breakdown
        print("\nValidation Status:")
        cursor.execute("""
            SELECT price_validation_status, COUNT(*) 
            FROM comprehensive_skins 
            WHERE current_price IS NOT NULL AND current_price > 0
            GROUP BY price_validation_status
            ORDER BY COUNT(*) DESC
        """)
        
        for status, count in cursor.fetchall():
            status_display = status if status else "unvalidated"
            percentage = (count / with_prices * 100) if with_prices > 0 else 0
            print(f"  {status_display}: {count:,} ({percentage:.1f}%)")
            
        # Recent validation activity
        if 'last_steam_check' in columns:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM comprehensive_skins 
                WHERE last_steam_check IS NOT NULL 
                AND date(last_steam_check) >= date('now', '-7 days')
            """)
            recent_validations = cursor.fetchone()[0]
            print(f"\nRecently validated (last 7 days): {recent_validations:,}")
        
    except Exception as e:
        print(f"❌ Error getting validation summary: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Reset price validation parameters in CS2 database')
    parser.add_argument('--db-path', default='data/comprehensive_skins.db',
                       help='Path to database file (default: data/comprehensive_skins.db)')
    parser.add_argument('--summary-only', action='store_true',
                       help='Show validation summary without resetting')
    parser.add_argument('--confirm', action='store_true',
                       help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level='INFO')
    
    # Check if database exists
    if not Path(args.db_path).exists():
        print(f"❌ Database not found: {args.db_path}")
        print("💡 Run build_comprehensive_database.py first to create the database")
        sys.exit(1)
    
    # Show summary
    show_validation_summary(args.db_path)
    
    if args.summary_only:
        return
    
    # Confirmation prompt unless --confirm is used
    if not args.confirm:
        print("\n⚠️  This will reset ALL price validation data!")
        print("   This means the next run will re-validate prices using Steam Market API")
        response = input("\nProceed with reset? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Reset cancelled")
            sys.exit(0)
    
    # Perform reset
    reset_price_validation(args.db_path)
    
    # Show updated summary
    print("\n" + "=" * 50)
    show_validation_summary(args.db_path)

if __name__ == "__main__":
    main()
