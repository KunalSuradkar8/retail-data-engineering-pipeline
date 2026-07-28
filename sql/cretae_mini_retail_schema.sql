-- 1. Create Schema
CREATE SCHEMA IF NOT EXISTS retail;

-- 2. Customer Domain Tables
CREATE TABLE IF NOT EXISTS retail.customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    signup_date DATE DEFAULT CURRENT_DATE,
    customer_segment VARCHAR(30) DEFAULT 'Regular',
    loyalty_tier VARCHAR(20) DEFAULT 'Bronze'
);

CREATE TABLE IF NOT EXISTS retail.addresses (
    address_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES retail.customers(customer_id),
    street_address VARCHAR(150) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    postal_code VARCHAR(15),
    country VARCHAR(50) DEFAULT 'India'
);

-- 3. Product & Inventory Domain Tables
CREATE TABLE IF NOT EXISTS retail.categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    parent_category_id INT,
    department_name VARCHAR(50),
    description TEXT
);

CREATE TABLE IF NOT EXISTS retail.suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    city VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS retail.products (
    product_id SERIAL PRIMARY KEY,
    category_id INT REFERENCES retail.categories(category_id),
    supplier_id INT REFERENCES retail.suppliers(supplier_id),
    product_name VARCHAR(100) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    unit_cost NUMERIC(10, 2) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Stores & Logistics Domain Tables
CREATE TABLE IF NOT EXISTS retail.stores (
    store_id SERIAL PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    store_type VARCHAR(30) DEFAULT 'Physical',
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    manager_name VARCHAR(50)
);

-- 5. Sales & Orders Domain Tables
CREATE TABLE IF NOT EXISTS retail.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES retail.customers(customer_id),
    store_id INT REFERENCES retail.stores(store_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    order_status VARCHAR(30) DEFAULT 'Completed',
    total_amount NUMERIC(12, 2) NOT NULL,
    discount_amount NUMERIC(10, 2) DEFAULT 0.00,
    tax_amount NUMERIC(10, 2) DEFAULT 0.00,
    shipping_amount NUMERIC(10, 2) DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS retail.order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES retail.orders(order_id),
    product_id INT REFERENCES retail.products(product_id),
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL,
    discount NUMERIC(10, 2) DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS retail.payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES retail.orders(order_id),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(30) NOT NULL,
    payment_status VARCHAR(30) DEFAULT 'Success',
    amount NUMERIC(12, 2) NOT NULL,
    transaction_reference VARCHAR(100),
    gateway_response VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS retail.shipments (
    shipment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES retail.orders(order_id),
    carrier_name VARCHAR(50) NOT NULL,
    tracking_number VARCHAR(100) UNIQUE,
    shipped_date TIMESTAMP,
    estimated_delivery DATE,
    delivery_status VARCHAR(30) DEFAULT 'In-Transit',
    shipping_cost NUMERIC(10, 2) DEFAULT 0.00
);
