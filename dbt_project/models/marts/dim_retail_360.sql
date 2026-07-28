with orders as (
    select * from {{ source('retail', 'orders') }}
),
customers as (
    select * from {{ source('retail', 'customers') }}
),
order_items as (
    select * from {{ source('retail', 'order_items') }}
),
products as (
    select * from {{ source('retail', 'products') }}
),
categories as (
    select * from {{ source('retail', 'categories') }}
),
suppliers as (
    select * from {{ source('retail', 'suppliers') }}
),
stores as (
    select * from {{ source('retail', 'stores') }}
),
payments as (
    select * from {{ source('retail', 'payments') }}
),
shipments as (
    select * from {{ source('retail', 'shipments') }}
)

select
    o.order_id,
    COALESCE(o.load_timestamp, CURRENT_TIMESTAMP) as order_date,
    COALESCE(o.order_status, 'Completed') as order_status,
    c.customer_id,
    concat(c.first_name, ' ', c.last_name) as customer_name,
    c.email as customer_email,
    c.loyalty_tier,
    st.store_name,
    st.city as store_city,
    p.product_name,
    p.sku,
    cat.category_name,
    cat.department_name,
    sup.supplier_name,
    oi.quantity,
    oi.unit_price,
    oi.subtotal,
    pay.payment_method,
    pay.payment_status,
    ship.carrier_name,
    ship.delivery_status
from orders o
left join customers c on cast(o.customer_id as text) = cast(c.customer_id as text)
left join stores st on cast(o.store_id as text) = cast(st.store_id as text)
left join order_items oi on cast(o.order_id as text) = cast(oi.order_id as text)
left join products p on cast(oi.product_id as text) = cast(p.product_id as text)
left join categories cat on cast(p.category_id as text) = cast(cat.category_id as text)
left join suppliers sup on cast(p.supplier_id as text) = cast(sup.supplier_id as text)
left join payments pay on cast(o.order_id as text) = cast(pay.order_id as text)
left join shipments ship on cast(o.order_id as text) = cast(ship.order_id as text)
