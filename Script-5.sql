SELECT
    sp.category,
    sp.sub_category,
    SUM(so.sales::NUMERIC) AS total_sales,
    SUM(so.profit::NUMERIC) AS total_profit,
    ROUND((SUM(so.profit::NUMERIC) / SUM(so.sales::NUMERIC)) * 100, 2) AS profit_margin_percentage
FROM superstore_order so
JOIN superstore_product sp ON so.product_id = sp.product_id
GROUP BY sp.category, sp.sub_category
ORDER BY total_profit DESC;

SELECT 
    sc.customer_name, 
    sc.segment,
    COUNT(DISTINCT so.order_id) AS total_orders,
    SUM(so.sales::NUMERIC) AS total_spend
FROM superstore_order so
JOIN superstore_customer sc  ON so.customer_id = sc.customer_id
GROUP BY sc.customer_name, sc.segment
ORDER BY total_spend DESC
LIMIT 10;

SELECT
    ps.product_name,
    ps.stock AS current_stock,
    COALESCE(SUM(o.quantity::NUMERIC), 0) AS total_units_sold
FROM product_stock ps
LEFT JOIN superstore_order so ON ps.product_id = so.product_id
GROUP BY ps.product_id, ps.product_name, ps.stock
ORDER BY ps.stock ASC;

SELECT 
    sp.category,
    sp.sub_category,
    ROUND(AVG(so.discount::NUMERIC) * 100, 2) AS avg_discount_percentage,
    ROUND(AVG(so.profit::NUMERIC), 2) AS avg_profit_per_item
FROM superstore_order so
JOIN superstore_product sp ON so.product_id = sp.product_id
GROUP BY sp.category, sp.sub_category
ORDER BY avg_profit_per_item DESC;

SELECT 
    ship_mode,
    COUNT(order_id) AS total_orders,
    ROUND(AVG(ship_date::DATE - order_date::DATE), 1) AS avg_shipping_days
FROM superstore_order
GROUP BY ship_mode
ORDER BY avg_shipping_days ASC;

SELECT 
    customer_name,
    COUNT(DISTINCT order_id) AS total_transactions,
    SUM(sales::NUMERIC) AS total_spent,
    ROUND(AVG(sales::NUMERIC), 2) AS avg_sales_per_item 
FROM superstore_order
GROUP BY customer_name
HAVING COUNT(DISTINCT order_id) > 5 
ORDER BY avg_sales_per_item desc;