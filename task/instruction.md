The file /app/data/generate_report.py is a Python 3 script that reads from a SQLite database at /app/data/sample_db.sqlite and writes a quarterly financial report to /app/output/report.csv. The script runs without errors but produces wrong numbers. Find and fix all defects.

The database has three tables:

orders: order_id, customer_id, order_date, order_status, discount_pct, subtotal
order_items: item_id, order_id, product_id, quantity, unit_price
shipping: shipment_id, order_id, shipping_cost, shipped_date

order_status has exactly four values: 'completed', 'pending', 'cancelled', 'refunded'. Revenue, discounts, shipping, and total_orders must include only orders with status 'completed' or 'pending'. NULL order_status must be excluded. NULL customer_id (foreign key) is possible and those orders are valid. Some orders have zero order_items rows — they count toward total_orders but contribute 0 revenue, 0 discount, 0 shipping. Some orders may not have a corresponding shipping record — those orders should still appear in the report with 0 shipping.

The report.csv must have these columns in this order: year, quarter, total_orders, total_revenue, total_discount, total_shipping. Float values must be rounded to 2 decimal places. Year and quarter are integers derived from order_date. Quarter 1 = Jan-Mar, 2 = Apr-Jun, 3 = Jul-Sep, 4 = Oct-Dec.

All logic in the script that is not buggy is authoritative — fix only the defects, do not redesign working parts.

Fix /app/data/generate_report.py, then copy your fixed version to /app/output/generate_report.py. The verifier will run this copy against a held-out database to verify your fix is general, not hardcoded. Run your fixed script to produce /app/output/report.csv — both files are graded.

Do not modify the database file. Do not create new Python scripts or data files; work within the existing script. Write all output to /app/output/report.csv and /app/output/generate_report.py.
