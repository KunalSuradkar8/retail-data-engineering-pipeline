import os
import sys
import random
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def seed_10_retail_tables():
    """
    Populates all 10 Enterprise Retail Tables with realistic domain test data in PostgreSQL.
    Respects Foreign Key relational integrity order:
    1. categories & suppliers -> 2. products -> 3. stores -> 4. customers & addresses -> 5. orders -> 6. order_items, payments & shipments
    """
    print("\n[INFO] Connecting to PostgreSQL Database to seed 10 Retail Tables...")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "retail_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "admin123")
    )
    cur = conn.cursor()

    try:
        # 1. Seed Categories
        print("1. Seeding 'retail.categories'...")
        categories_data = [
            ('Electronics', 'Technology', 'Gadgets and electronic items'),
            ('Apparel', 'Fashion', 'Clothing and garments'),
            ('Grocery', 'Supermarket', 'Daily essentials and food items'),
            ('Home & Kitchen', 'Home Living', 'Appliances and cookware')
        ]
        for cname, dept, desc in categories_data:
            cur.execute("""
                INSERT INTO retail.categories (category_name, department_name, description)
                VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;
            """, (cname, dept, desc))
        conn.commit()

        cur.execute("SELECT category_id FROM retail.categories;")
        category_ids = [r[0] for r in cur.fetchall()]

        # 2. Seed Suppliers
        print("2. Seeding 'retail.suppliers'...")
        suppliers_data = [
            ('Reliance Retail Wholesale', 'Rajesh Sharma', 'contact@relianceretail.com', '9820012345', 'Mumbai'),
            ('Tata Consumer Products', 'Ananya Deshmukh', 'info@tataconsumer.com', '9811098765', 'Pune'),
            ('Global Electronics Ltd', 'Vikram Malhotra', 'sales@globalelectronics.com', '9899011223', 'Bangalore')
        ]
        for sname, cname, email, phone, city in suppliers_data:
            cur.execute("""
                INSERT INTO retail.suppliers (supplier_name, contact_name, email, phone, city)
                VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
            """, (sname, cname, email, phone, city))
        conn.commit()

        cur.execute("SELECT supplier_id FROM retail.suppliers;")
        supplier_ids = [r[0] for r in cur.fetchall()]

        # 3. Seed Products
        print("3. Seeding 'retail.products'...")
        if category_ids and supplier_ids:
            products_data = [
                ('ProBook Laptop 15-inch', 'SKU-LAP-001', 42000.00, 55000.00, 150),
                ('Wireless Noise Cancelling Headphones', 'SKU-AUD-002', 4500.00, 7999.00, 300),
                ('Cotton Casual Shirt XL', 'SKU-SHI-003', 600.00, 1499.00, 500),
                ('Organic Whole Wheat Atta 10kg', 'SKU-GRO-004', 320.00, 450.00, 1000),
                ('Stainless Steel Air Fryer 4L', 'SKU-KIT-005', 3800.00, 5999.00, 200)
            ]
            for pname, sku, ucost, uprice, stock in products_data:
                cat_id = random.choice(category_ids)
                sup_id = random.choice(supplier_ids)
                cur.execute("""
                    INSERT INTO retail.products (category_id, supplier_id, product_name, sku, unit_cost, unit_price, stock_quantity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (sku) DO NOTHING;
                """, (cat_id, sup_id, pname, sku, ucost, uprice, stock))
            conn.commit()

        # 4. Seed Stores
        print("4. Seeding 'retail.stores'...")
        stores_data = [
            ('Mumbai Flagship MegaStore', 'Physical', 'Mumbai', 'Maharashtra', 'Sanjay Verma'),
            ('Pune City Center Store', 'Physical', 'Pune', 'Maharashtra', 'Meera Kulkarni'),
            ('India Online E-Commerce Warehouse', 'Online Hub', 'Bangalore', 'Karnataka', 'Arjun Mehta')
        ]
        for sname, stype, city, state, mgr in stores_data:
            cur.execute("""
                INSERT INTO retail.stores (store_name, store_type, city, state, manager_name)
                VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
            """, (sname, stype, city, state, mgr))
        conn.commit()

        # 5. Seed Customers & Addresses
        print("5. Seeding 'retail.customers' & 'retail.addresses'...")
        customers_data = [
            ('Kunal', 'Suradkar', 'kunal.suradkar@email.com', '9876543210', 'Gold'),
            ('Priya', 'Patel', 'priya.patel@email.com', '9812345678', 'Silver'),
            ('Rahul', 'Deshmukh', 'rahul.d@email.com', '9988776655', 'Bronze'),
            ('Neha', 'Gupta', 'neha.gupta@email.com', '9765432109', 'Platinum'),
            ('Amit', 'Joshi', 'amit.j@email.com', '9898989898', 'Silver')
        ]
        
        for fn, ln, email, phone, tier in customers_data:
            cur.execute("""
                INSERT INTO retail.customers (first_name, last_name, email, phone, loyalty_tier)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING;
            """, (fn, ln, email, phone, tier))
        conn.commit()

        # 6. Seed Orders, Order Items, Payments & Shipments
        print("6. Seeding Orders, Order Items, Payments & Shipments...")
        cur.execute("SELECT customer_id FROM retail.customers;")
        cust_ids = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT product_id, unit_price FROM retail.products;")
        products = cur.fetchall()

        cur.execute("SELECT store_id FROM retail.stores;")
        store_ids = [r[0] for r in cur.fetchall()]

        if cust_ids and products and store_ids:
            for i in range(10):
                c_id = random.choice(cust_ids)
                s_id = random.choice(store_ids)
                prod_id, price = random.choice(products)
                qty = random.randint(1, 4)
                total = float(price) * qty
                
                # Insert Order
                cur.execute("""
                    INSERT INTO retail.orders (customer_id, store_id, total_amount, order_status)
                    VALUES (%s, %s, %s, 'Completed') RETURNING order_id;
                """, (c_id, s_id, total))
                order_id = cur.fetchone()[0]

                # Insert Order Item
                cur.execute("""
                    INSERT INTO retail.order_items (order_id, product_id, quantity, unit_price, subtotal)
                    VALUES (%s, %s, %s, %s, %s);
                """, (order_id, prod_id, qty, price, total))

                # Insert Payment
                method = random.choice(['UPI_GPay', 'Credit_Card', 'NetBanking'])
                cur.execute("""
                    INSERT INTO retail.payments (order_id, payment_method, amount, transaction_reference)
                    VALUES (%s, %s, %s, %s);
                """, (order_id, method, total, f"TXN-{random.randint(100000, 999999)}"))

                # Insert Shipment
                carrier = random.choice(['BlueDart', 'Delhivery', 'DTDC'])
                cur.execute("""
                    INSERT INTO retail.shipments (order_id, carrier_name, tracking_number, delivery_status)
                    VALUES (%s, %s, %s, 'Delivered');
                """, (order_id, carrier, f"TRK-{random.randint(1000000, 9999999)}"))

        conn.commit()
        print("\n[SUCCESS] All 10 Enterprise Retail Tables successfully populated with seed data!")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to seed database: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_10_retail_tables()
