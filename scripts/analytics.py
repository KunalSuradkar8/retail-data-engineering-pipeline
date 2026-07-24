import os
import sys

# Direct execution साठी प्रोजेक्ट रूट sys.path मध्ये जोडतो
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config_loader import ConfigLoader
from utils.database import PostgresConnectionManager

def generate_analytics_report():
    """
    Generates Executive Business Reports and KPIs from PostgreSQL database.
    """
    config = ConfigLoader()
    db_config = config.db_credentials
    
    print("\n" + "="*60)
    print(" 📊 RETAIL BUSINESS ANALYTICS & EXECUTIVE REPORT")
    print("="*60)
    
    try:
        with PostgresConnectionManager(db_config) as db:
            cursor = db.cursor
            
            # Query 1: Total Revenue and Total Orders
            cursor.execute("""
                SELECT COUNT(*) as total_orders, SUM(total_amount) as total_revenue
                FROM retail.orders;
            """)
            orders_count, total_revenue = cursor.fetchone()
            print(f"\n📈 OVERALL BUSINESS SUMMARY:")
            print(f"   • Total Processed Orders : {orders_count or 0}")
            print(f"   • Total Generated Revenue: ${total_revenue:,.2f}" if total_revenue else "   • Total Revenue: $0.00")
            
            # Query 2: Top 5 Best-Selling Products by Revenue
            print(f"\n🏆 TOP 5 BEST-SELLING PRODUCTS (By Revenue):")
            print("   " + "-"*48)
            print("   Product ID  |  Total Qty Sold  |  Total Revenue")
            print("   " + "-"*48)
            cursor.execute("""
                SELECT product_id, SUM(quantity) as total_qty, SUM(total_amount) as revenue
                FROM retail.orders
                GROUP BY product_id
                ORDER BY revenue DESC
                LIMIT 5;
            """)
            top_products = cursor.fetchall()
            for prod_id, qty, rev in top_products:
                print(f"   {prod_id:<12} |  {qty:<15} |  ${rev:,.2f}")
                
            # Query 3: Top 5 Highest Spending Customers
            print(f"\n💎 TOP 5 VIP CUSTOMERS (By Total Spent):")
            print("   " + "-"*48)
            print("   Customer ID |  Orders Count    |  Total Spent")
            print("   " + "-"*48)
            cursor.execute("""
                SELECT customer_id, COUNT(order_id) as order_count, SUM(total_amount) as spent
                FROM retail.orders
                GROUP BY customer_id
                ORDER BY spent DESC
                LIMIT 5;
            """)
            top_customers = cursor.fetchall()
            for cust_id, count, spent in top_customers:
                print(f"   {cust_id:<12} |  {count:<15} |  ${spent:,.2f}")
                
            print("\n" + "="*60 + "\n")
            
    except Exception as e:
        print(f"\n❌ Error generating analytics report: {e}")

if __name__ == "__main__":
    generate_analytics_report()
