#!/usr/bin/env python3
"""Monthly financial report generator.

Reads from the SQLite database and writes a CSV report to /app/output/report.csv.
"""

import sqlite3
import csv
import os

DB_PATH = "/app/data/sample_db.sqlite"
OUTPUT_DIR = "/app/output"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "report.csv")


def generate_report():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # --- BUG 1: Discount fan-out ---
    # The LEFT JOIN to order_items multiplies order-level discount rows.
    # discount_pct * subtotal is per-order, but JOIN fans it out per line item.
    discount_query = """
        SELECT
            CAST(strftime('%Y', o.order_date) AS INTEGER) as year,
            ((CAST(strftime('%m', o.order_date) AS INTEGER) - 1) / 3) + 1 as quarter,
            COUNT(DISTINCT o.order_id) as order_count,
            SUM(oi.quantity * oi.unit_price) as revenue,
            SUM(o.discount_pct * o.subtotal) as discount_total
        FROM orders o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY year, quarter
    """

    # --- BUG 4: Performance anti-pattern ---
    # This query uses a correlated subquery that causes repeated inner scans.
    # EXPLAIN QUERY PLAN will reveal SCAN orders without a proper index.
    # Fix: rewrite to a JOIN + derived table, and create an index.
    shipping_query = """
        SELECT
            CAST(strftime('%Y', o.order_date) AS INTEGER) as year,
            ((CAST(strftime('%m', o.order_date) AS INTEGER) - 1) / 3) + 1 as quarter,
            SUM(s.shipping_cost) as shipping_total
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN shipping s ON o.order_id = s.order_id
        WHERE o.order_date >= '2023-01-01'
        GROUP BY year, quarter
    """

    discount_rows = conn.execute(discount_query).fetchall()
    shipping_rows = conn.execute(shipping_query).fetchall()

    # Index shipping rows by (year, quarter)
    shipping_map = {}
    for row in shipping_rows:
        key = (row["year"], row["quarter"])
        # --- BUG 2: Shipping summed at line-item grain ---
        # shipping_cost is per-order but grouped with order_items join
        # causing duplication. Stored as-is (buggy).
        shipping_map[key] = row["shipping_total"]

    # --- BUG 3: No status filter ---
    # The discount query doesn't filter out cancelled/refunded orders.
    # Fix: add WHERE o.order_status IN ('completed', 'pending')

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "quarter", "total_orders", "total_revenue",
                         "total_discount", "total_shipping"])

        for row in discount_rows:
            yr, qtr = row["year"], row["quarter"]
            shipping = shipping_map.get((yr, qtr), 0.0)
            writer.writerow([
                yr, qtr,
                row["order_count"],
                round(row["revenue"], 2),
                round(row["discount_total"], 2),
                round(shipping, 2),
            ])


if __name__ == "__main__":
    generate_report()
    print("Report written to", OUTPUT_PATH)
