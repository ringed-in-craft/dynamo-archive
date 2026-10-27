The file /app/data/REPORT_SPEC.md is the complete and authoritative specification for a quarterly financial report. /app/data/generate_report.py is a Python 3 script that attempts to implement this specification by reading from a SQLite database at /app/data/sample_db.sqlite and writing output to /app/output/report.csv. The script runs without errors but does not fully conform to the specification. Find and fix all deviations from the spec.

The database has three tables:

orders: order_id, customer_id, order_date, order_status, discount_pct, subtotal
order_items: item_id, order_id, product_id, quantity, unit_price
shipping: shipment_id, order_id, shipping_cost, shipped_date

order_status has exactly four values: 'completed', 'pending', 'cancelled', 'refunded'. NULL order_status is possible and must be excluded. NULL customer_id is possible and those orders are valid.

The spec document at /app/data/REPORT_SPEC.md defines all requirements: output columns, included orders, revenue calculation, discount calculation, shipping calculation, and rounding. Read it in full — every rule in the spec must be implemented, even those that do not affect the sample data. The spec is the authoritative reference; if the script contradicts the spec, the spec wins.

Fix /app/data/generate_report.py to fully conform to /app/data/REPORT_SPEC.md, then copy your fixed version to /app/output/generate_report.py. The verifier will run this copy against a held-out database to verify correctness. Run your fixed script to produce /app/output/report.csv — both files are graded.

Do not modify the database file. Do not create new Python scripts or data files; work within the existing script. Write all output to /app/output/report.csv and /app/output/generate_report.py.
