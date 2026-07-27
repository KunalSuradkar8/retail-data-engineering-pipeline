with raw_orders as (
    select * from {{ source('retail', 'orders') }}
)

select
    cast(order_id as integer) as order_id,
    cast(customer_id as varchar(50)) as customer_id,
    cast(product_id as varchar(50)) as product_id,
    cast(quantity as integer) as quantity,
    cast(price as numeric(10, 2)) as unit_price,
    cast(total_amount as numeric(12, 2)) as total_amount,
    cast(load_timestamp as timestamp) as loaded_at
from raw_orders
