#!/usr/bin/env python3
"""Quarterly financial report generator — FIXED.

Reads from the SQLite database and writes a CSV report to /app/output/report.csv.
All bugs fixed: pre-aggregation at correct grain, status filtering, and index creation.
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

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_date_cust "
        "ON orders(order_date, customer_id)"
    )

    rows = conn.execute("""
        SELECT
            CAST(strftime('%Y', o.order_date) AS INTEGER) as year,
            ((CAST(strftime('%m', o.order_date) AS INTEGER) - 1) / 3) + 1 as quarter,
            COUNT(DISTINCT o.order_id) as total_orders,
            ROUND(SUM(COALESCE(item_revenue.total, 0)), 2) as total_revenue,
            ROUND(SUM(CASE WHEN o.order_status IN ('completed', 'pending')
                       THEN o.discount_pct * o.subtotal ELSE 0 END), 2) as total_discount,
            ROUND(SUM(COALESCE(order_shipping.cost, 0)), 2) as total_shipping
        FROM orders o
        LEFT JOIN (
            SELECT order_id, SUM(quantity * unit_price) as total
            FROM order_items
            GROUP BY order_id
        ) item_revenue ON o.order_id = item_revenue.order_id
        LEFT JOIN (
            SELECT order_id, shipping_cost as cost
            FROM shipping
        ) order_shipping ON o.order_id = order_shipping.order_id
        WHERE o.order_status IN ('completed', 'pending')
        GROUP BY year, quarter
        ORDER BY year, quarter
    """).fetchall()

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "quarter", "total_orders", "total_revenue",
                         "total_discount", "total_shipping"])
        for row in rows:
            writer.writerow([
                row["year"], row["quarter"],
                row["total_orders"],
                row["total_revenue"],
                row["total_discount"],
                row["total_shipping"],
            ])

    conn.close()
    print("Report written to", OUTPUT_PATH)


if __name__ == "__main__":
    generate_report()
