"""
ARMG Phase 1: Deterministic Enterprise Data Warehouse Seeder.

This script populates the PostgreSQL Star Schema (db/schema.sql) with realistic,
reproducible analytical data using a fixed NumPy seed (seed=42).

Tables populated:
- dim_time: 365 daily records for calendar year 2025.
- dim_geography: 6 enterprise regions and zones.
- dim_product: 8 multi-category hardware and software products.
- fact_sales_performance: Exactly 2,000 analytical fact transactions.

Execution is idempotent: it executes db/schema.sql to drop/recreate tables
before seeding.
"""

import os
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "armg_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")


def get_connection():
    """Establish and return a connection to PostgreSQL."""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def apply_schema(cursor):
    """Execute db/schema.sql to ensure clean, idempotent table structures."""
    schema_path = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        ddl_sql = f.read()
    cursor.execute(ddl_sql)


def seed_dim_time(cursor) -> list[int]:
    """Generate and insert 365 daily rows for calendar year 2025."""
    start_date = date(2025, 1, 1)
    time_keys = []
    rows = []

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for i in range(365):
        curr_date = start_date + timedelta(days=i)
        time_key = int(curr_date.strftime("%Y%m%d"))
        day_of_week = day_names[curr_date.weekday()]
        month = curr_date.month
        quarter = (month - 1) // 3 + 1
        year = curr_date.year

        time_keys.append(time_key)
        rows.append((time_key, curr_date, day_of_week, month, quarter, year))

    query = """
    INSERT INTO dim_time (time_key, full_date, day_of_week, calendar_month, calendar_quarter, calendar_year)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    execute_batch(cursor, query, rows)
    return time_keys


def seed_dim_geography(cursor) -> list[int]:
    """Insert 6 enterprise geographic zones."""
    geo_data = [
        (1, "North America", "East Zone", "Enterprise"),
        (2, "North America", "West Zone", "Enterprise"),
        (3, "EMEA", "UK & Ireland", "Commercial"),
        (4, "EMEA", "DACH", "Commercial"),
        (5, "APAC", "Southeast Asia", "Emerging"),
        (6, "APAC", "ANZ", "Enterprise"),
    ]
    query = """
    INSERT INTO dim_geography (geo_key, region, zone, market_type)
    VALUES (%s, %s, %s, %s);
    """
    execute_batch(cursor, query, geo_data)
    return [g[0] for g in geo_data]


def seed_dim_product(cursor) -> dict[int, float]:
    """Insert 8 enterprise products across hardware and software categories."""
    product_data = [
        (1, "Cloud Core Suite", "Software", "SaaS", 150.00),
        (2, "SecureGate Firewall", "Hardware", "Network Security", 450.00),
        (3, "DataVault Enterprise", "Software", "Storage", 320.00),
        (4, "EdgeCompute Gateway", "Hardware", "Edge Devices", 280.00),
        (5, "NeuralEngine Platform", "Software", "AI Platform", 80.00),
        (6, "CyberShield Endpoint", "Software", "Security", 120.00),
        (7, "FiberSwitch Pro", "Hardware", "Networking", 500.00),
        (8, "Analytics Insights Pro", "Software", "Business Intelligence", 200.00),
    ]
    query = """
    INSERT INTO dim_product (product_key, product_name, category, sub_category, unit_cost)
    VALUES (%s, %s, %s, %s, %s);
    """
    execute_batch(cursor, query, product_data)
    return {p[0]: p[4] for p in product_data}


def seed_fact_sales_performance(cursor, time_keys: list[int], geo_keys: list[int], product_costs: dict[int, float], count: int = 2000):
    """Generate and insert exactly 2,000 deterministic sales fact transactions."""
    product_keys = list(product_costs.keys())
    
    # Deterministic generation using NumPy seed=42
    np.random.seed(42)

    selected_times = np.random.choice(time_keys, size=count)
    selected_geos = np.random.choice(geo_keys, size=count)
    selected_products = np.random.choice(product_keys, size=count)
    units_sold_arr = np.random.randint(1, 51, size=count)  # 1 to 50 units
    markups = np.random.uniform(1.35, 2.10, size=count)     # Markup factor
    discount_rates = np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], p=[0.40, 0.25, 0.15, 0.12, 0.08], size=count)

    fact_rows = []
    for i in range(count):
        fact_key = i + 1
        t_key = int(selected_times[i])
        g_key = int(selected_geos[i])
        p_key = int(selected_products[i])
        units = int(units_sold_arr[i])
        
        unit_cost = float(product_costs[p_key])
        unit_price = round(float(unit_cost * markups[i]), 2)
        gross_revenue = round(float(units * unit_price), 2)
        discount_applied = round(float(gross_revenue * discount_rates[i]), 2)
        net_revenue = float(gross_revenue - discount_applied)
        cogs = round(float(units * unit_cost), 2)
        net_profit = round(float(net_revenue - cogs), 2)

        fact_rows.append((
            fact_key,
            t_key,
            g_key,
            p_key,
            units,
            gross_revenue,
            discount_applied,
            net_profit,
        ))

    query = """
    INSERT INTO fact_sales_performance (
        fact_key, time_key, geo_key, product_key, units_sold, gross_revenue, discount_applied, net_profit
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    execute_batch(cursor, query, fact_rows, page_size=500)


def seed_database():
    """Main database seeding routine."""
    conn = get_connection()
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            print("Applying schema from db/schema.sql...")
            apply_schema(cur)

            print("Seeding dim_time (365 rows)...")
            time_keys = seed_dim_time(cur)

            print("Seeding dim_geography (6 rows)...")
            geo_keys = seed_dim_geography(cur)

            print("Seeding dim_product (8 rows)...")
            product_costs = seed_dim_product(cur)

            print("Seeding fact_sales_performance (exactly 2,000 rows, seed=42)...")
            seed_fact_sales_performance(cur, time_keys, geo_keys, product_costs, count=2000)

            # Verification
            cur.execute("SELECT COUNT(*) FROM fact_sales_performance;")
            fact_count = cur.fetchone()[0]
            assert fact_count == 2000, f"Expected 2,000 rows in fact_sales_performance, got {fact_count}"

        conn.commit()
        print(f"Database seeded successfully. Total fact rows: {fact_count}")
    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()
