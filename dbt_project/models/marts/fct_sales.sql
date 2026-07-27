with staging_orders as (
    select * from {{ ref('stg_orders') }}
)

select
    order_id,
    customer_id,
    product_id,
    quantity,
    unit_price,
    total_amount,
    date(loaded_at) as sales_date
from staging_orders
