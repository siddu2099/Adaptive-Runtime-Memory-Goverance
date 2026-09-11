-- ==============================================================================
-- Adaptive Runtime Memory Governance (ARMG)
-- Phase 1: Enterprise PostgreSQL Star Schema Data Warehouse
-- ==============================================================================

-- Drop tables in reverse order of foreign key dependencies for idempotency
DROP TABLE IF EXISTS fact_sales_performance CASCADE;
DROP TABLE IF EXISTS dim_time CASCADE;
DROP TABLE IF EXISTS dim_geography CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;

-- ------------------------------------------------------------------------------
-- 1. Dimension: Time
-- ------------------------------------------------------------------------------
CREATE TABLE dim_time (
    time_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_week VARCHAR(20) NOT NULL,
    calendar_month INTEGER NOT NULL CHECK (calendar_month BETWEEN 1 AND 12),
    calendar_quarter INTEGER NOT NULL CHECK (calendar_quarter BETWEEN 1 AND 4),
    calendar_year INTEGER NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Dimension: Geography
-- ------------------------------------------------------------------------------
CREATE TABLE dim_geography (
    geo_key INTEGER PRIMARY KEY,
    region VARCHAR(100) NOT NULL,
    zone VARCHAR(100) NOT NULL,
    market_type VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 3. Dimension: Product
-- ------------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100) NOT NULL,
    unit_cost NUMERIC(10, 2) NOT NULL CHECK (unit_cost >= 0)
);

-- ------------------------------------------------------------------------------
-- 4. Fact: Sales Performance
-- ------------------------------------------------------------------------------
CREATE TABLE fact_sales_performance (
    fact_key INTEGER PRIMARY KEY,
    time_key INTEGER NOT NULL REFERENCES dim_time(time_key) ON DELETE RESTRICT,
    geo_key INTEGER NOT NULL REFERENCES dim_geography(geo_key) ON DELETE RESTRICT,
    product_key INTEGER NOT NULL REFERENCES dim_product(product_key) ON DELETE RESTRICT,
    units_sold INTEGER NOT NULL CHECK (units_sold >= 0),
    gross_revenue NUMERIC(12, 2) NOT NULL CHECK (gross_revenue >= 0),
    discount_applied NUMERIC(10, 2) NOT NULL CHECK (discount_applied >= 0),
    net_profit NUMERIC(12, 2) NOT NULL
);

-- Create indexes on foreign keys to optimize analytical query joins
CREATE INDEX idx_fact_sales_time_key ON fact_sales_performance(time_key);
CREATE INDEX idx_fact_sales_geo_key ON fact_sales_performance(geo_key);
CREATE INDEX idx_fact_sales_product_key ON fact_sales_performance(product_key);
