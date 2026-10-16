# ARMG Synthetic Database Methodology & Schema Specification

**Document Version:** 1.0  
**Status:** Verified Reference  
**Database System:** PostgreSQL 18.1 (`localhost:5432`, `armg_db`)  
**Source Code References:** [`db/schema.sql`](file:///c:/Users/siddu/Pictures/armg%20main/db/schema.sql), [`scripts/seed_warehouse.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/seed_warehouse.py), [`benchmark/queries.json`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/queries.json)

---

## 1. Executive Summary & Purpose

The Adaptive Runtime Memory Governance (ARMG) framework utilizes a controlled synthetic relational data warehouse modeled as a classic star schema in PostgreSQL 18.1. 

The primary objective of this database is to provide a **deterministic, repeatable, and ground-truth-verifiable execution environment** for evaluating LLM-driven Text-to-SQL generation, AST guardrail enforcement, runtime error diagnosis, and bounded self-correction repair loops.

---

## 2. Warehouse Schema Architecture & Topology

The warehouse consists of exactly **four tables**: three dimension tables and one central fact table.

```
       +--------------------+
       |      dim_time      | (365 rows)
       |--------------------|
       | PK: time_key       |
       +---------+----------+
                 | 1
                 |
                 | N
       +---------v----------------+              +--------------------+
       |  fact_sales_performance  | 1          N |   dim_geography    |
       |--------------------------+--------------< |--------------------|
       | PK: fact_key             |              | PK: geo_key        |
       | FK: time_key             |              +--------------------+
       | FK: geo_key              |
       | FK: product_key          | 1          N +--------------------+
       +---------+----------------+--------------< |    dim_product     |
                 |                               |--------------------|
                 +-------------------------------+ PK: product_key     |
                                                 +--------------------+
```

### Table 1: `dim_time` (Date Dimension)
* **Row Count:** 365 rows (calendar year 2025: `2025-01-01` to `2025-12-31`).
* **Primary Key:** `time_key` (`INTEGER`, formatted as `YYYYMMDD`, e.g., `20250101`).
* **Columns & Constraints:**
  * `time_key` (`INTEGER PRIMARY KEY`)
  * `full_date` (`DATE NOT NULL UNIQUE`)
  * `day_of_week` (`VARCHAR(20) NOT NULL` — e.g., 'Monday', 'Tuesday')
  * `calendar_month` (`INTEGER NOT NULL CHECK (calendar_month BETWEEN 1 AND 12)`)
  * `calendar_quarter` (`INTEGER NOT NULL CHECK (calendar_quarter BETWEEN 1 AND 4)`)
  * `calendar_year` (`INTEGER NOT NULL` — all records are 2025)

### Table 2: `dim_geography` (Geographic Dimension)
* **Row Count:** 6 rows.
* **Primary Key:** `geo_key` (`INTEGER PRIMARY KEY`, values 1 to 6).
* **Columns & Constraints:**
  * `geo_key` (`INTEGER PRIMARY KEY`)
  * `region` (`VARCHAR(100) NOT NULL`)
  * `zone` (`VARCHAR(100) NOT NULL`)
  * `market_type` (`VARCHAR(50) NOT NULL`)
* **Static Content (`scripts/seed_warehouse.py:83-90`):**
  1. `(1, 'North America', 'East Zone', 'Enterprise')`
  2. `(2, 'North America', 'West Zone', 'Enterprise')`
  3. `(3, 'EMEA', 'UK & Ireland', 'Commercial')`
  4. `(4, 'EMEA', 'DACH', 'Commercial')`
  5. `(5, 'APAC', 'Southeast Asia', 'Emerging')`
  6. `(6, 'APAC', 'ANZ', 'Enterprise')`

### Table 3: `dim_product` (Product Dimension)
* **Row Count:** 8 rows.
* **Primary Key:** `product_key` (`INTEGER PRIMARY KEY`, values 1 to 8).
* **Columns & Constraints:**
  * `product_key` (`INTEGER PRIMARY KEY`)
  * `product_name` (`VARCHAR(150) NOT NULL`)
  * `category` (`VARCHAR(100) NOT NULL` — 'Software' or 'Hardware')
  * `sub_category` (`VARCHAR(100) NOT NULL` — 'SaaS', 'Network Security', 'Storage', 'Edge Devices', 'AI Platform', 'Security', 'Networking', 'Business Intelligence')
  * `unit_cost` (`NUMERIC(10, 2) NOT NULL CHECK (unit_cost >= 0)`)
* **Static Content (`scripts/seed_warehouse.py:101-110`):**
  1. `(1, 'Cloud Core Suite', 'Software', 'SaaS', 150.00)`
  2. `(2, 'SecureGate Firewall', 'Hardware', 'Network Security', 450.00)`
  3. `(3, 'DataVault Enterprise', 'Software', 'Storage', 320.00)`
  4. `(4, 'EdgeCompute Gateway', 'Hardware', 'Edge Devices', 280.00)`
  5. `(5, 'NeuralEngine Platform', 'Software', 'AI Platform', 80.00)`
  6. `(6, 'CyberShield Endpoint', 'Software', 'Security', 120.00)`
  7. `(7, 'FiberSwitch Pro', 'Hardware', 'Networking', 500.00)`
  8. `(8, 'Analytics Insights Pro', 'Software', 'Business Intelligence', 200.00)`

### Table 4: `fact_sales_performance` (Central Fact Table)
* **Row Count:** Exactly 2,000 transactions.
* **Primary Key:** `fact_key` (`INTEGER PRIMARY KEY`, values 1 to 2000).
* **Foreign Key Constraints:**
  * `time_key REFERENCES dim_time(time_key) ON DELETE RESTRICT`
  * `geo_key REFERENCES dim_geography(geo_key) ON DELETE RESTRICT`
  * `product_key REFERENCES dim_product(product_key) ON DELETE RESTRICT`
* **Numerical Metrics & Constraints:**
  * `units_sold` (`INTEGER NOT NULL CHECK (units_sold >= 0)`)
  * `gross_revenue` (`NUMERIC(12, 2) NOT NULL CHECK (gross_revenue >= 0)`)
  * `discount_applied` (`NUMERIC(10, 2) NOT NULL CHECK (discount_applied >= 0)`)
  * `net_profit` (`NUMERIC(12, 2) NOT NULL`)
* **Indexes (`db/schema.sql:60-62`):**
  * `idx_fact_sales_time_key ON fact_sales_performance(time_key)`
  * `idx_fact_sales_geo_key ON fact_sales_performance(geo_key)`
  * `idx_fact_sales_product_key ON fact_sales_performance(product_key)`

---

## 3. Total Row Count Verification

| Table Name | Entity Type | Verified Row Count | Source Verification |
| :--- | :--- | :---: | :--- |
| `dim_time` | Dimension | **365** | `scripts/seed_warehouse.py:62` |
| `dim_geography` | Dimension | **6** | `scripts/seed_warehouse.py:83` |
| `dim_product` | Dimension | **8** | `scripts/seed_warehouse.py:101` |
| `fact_sales_performance` | Fact | **2,000** | `scripts/seed_warehouse.py:119, 192` |
| **Total Warehouse Rows** | | **2,379** | Exact sum of all four relations |

---

## 4. Synthetic Data Generation Process (`scripts/seed_warehouse.py`)

The fact data is synthesized deterministically using Python and NumPy.

### Random Number Generation Setup
* **RNG Library:** `numpy.random`
* **Random Seed:** `np.random.seed(42)` (fixed constant)
* **Transaction Count:** `count = 2000`

### Foreign Key & Transaction Sampling
1. **Time Selection:** `selected_times = np.random.choice(time_keys, size=count)`  
   *Uniform random sampling with replacement from the 365 2025 date keys.*
2. **Geography Selection:** `selected_geos = np.random.choice(geo_keys, size=count)`  
   *Uniform random sampling with replacement from geo keys 1 to 6.*
3. **Product Selection:** `selected_products = np.random.choice(product_keys, size=count)`  
   *Uniform random sampling with replacement from product keys 1 to 8.*
4. **Units Sold:** `units_sold_arr = np.random.randint(1, 51, size=count)`  
   *Discrete uniform integer range: $1 \le \text{units\_sold} \le 50$.*
5. **Markup Multiplier:** `markups = np.random.uniform(1.35, 2.10, size=count)`  
   *Continuous uniform distribution: $[1.35, 2.10]$.*
6. **Discount Rate:**  
   `discount_rates = np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], p=[0.40, 0.25, 0.15, 0.12, 0.08], size=count)`  
   *Categorical probability distribution:*
   - `0% discount`: 40% probability
   - `5% discount`: 25% probability
   - `10% discount`: 15% probability
   - `15% discount`: 12% probability
   - `20% discount`: 8% probability

### Financial Calculation Rules & Formulas
For transaction index $i \in \{0, \dots, 1999\}$:
1. `unit_cost = float(product_costs[p_key])`
2. `unit_price = round(unit_cost * markups[i], 2)`
3. `gross_revenue = round(units * unit_price, 2)`
4. `discount_applied = round(gross_revenue * discount_rates[i], 2)`
5. `net_revenue = gross_revenue - discount_applied`
6. `cogs = round(units * unit_cost, 2)` (Cost of Goods Sold)
7. `net_profit = round(net_revenue - cogs, 2)`

All monetary values are rounded to 2 decimal places before database insertion, matching PostgreSQL `NUMERIC(10, 2)` and `NUMERIC(12, 2)` specifications.

---

## 5. Database Rebuild and Reset Procedure

The database is built or reset by executing:

```bash
python scripts/seed_warehouse.py
```

### Destructive Behavior & Reset Protocol
* The seeder invokes `apply_schema(cur)`, which reads and executes [`db/schema.sql`](file:///c:/Users/siddu/Pictures/armg%20main/db/schema.sql).
* Lines 7–10 of `db/schema.sql` contain:
  ```sql
  DROP TABLE IF EXISTS fact_sales_performance CASCADE;
  DROP TABLE IF EXISTS dim_time CASCADE;
  DROP TABLE IF EXISTS dim_geography CASCADE;
  DROP TABLE IF EXISTS dim_product CASCADE;
  ```
* **Destructive Impact:** Running `seed_warehouse.py` **unconditionally drops all four tables**, wiping all existing rows, manual query logs, views, or indexes, and re-seeds the pristine 2,379 rows.
* **Caution:** Do NOT run this script during evaluation runs or manual testing sessions unless an intentional database reset is required.

---

## 6. How the 25 Benchmark Queries Exercise the Schema

The benchmark suite ([`benchmark/queries.json`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/queries.json)) contains 25 canonical evaluation queries partitioned into 4 distinct categories:

### Category A: Simple Aggregations & Groupings (Q01–Q05)
* **Focus:** Baseline SQL aggregation syntax, single-dimension joins, date filtering.
* **Schema Coverage:**
  * Q01: Fact table aggregation (`SUM(gross_revenue)`).
  * Q02: 1-hop join `fact_sales_performance` $\bowtie$ `dim_product` (`SUM(units_sold)` by `category`).
  * Q03: Fact table aggregation (`AVG(discount_applied)`).
  * Q04: 1-hop join `fact_sales_performance` $\bowtie$ `dim_geography` (`COUNT(*)` by `market_type`).
  * Q05: 1-hop join `fact_sales_performance` $\bowtie$ `dim_time` (`SUM(net_profit)` by `calendar_quarter` where `calendar_year = 2025`).

### Category B: Multi-Table Analytical Joins (Q06–Q13)
* **Focus:** Star-schema multi-hop joins (2 to 3 dimensions), composite `GROUP BY`, and multi-attribute `WHERE` filters.
* **Schema Coverage:**
  * Q06: Join with `dim_geography` (`region`).
  * Q07: Multi-join with `dim_product` and `dim_geography` (`category`, `market_type`).
  * Q08: Multi-join with `dim_geography` and `dim_time` (`region`, `calendar_month`).
  * Q09: Join with `dim_geography` and `dim_product` with string predicate (`category = 'Hardware'`).
  * Q10: Join with `dim_product` and `dim_geography` with predicate (`market_type = 'Enterprise'`).
  * Q11: Join with `dim_time` and `dim_geography` with predicate (`market_type = 'Commercial'`).
  * Q12: Join with `dim_product` and `dim_geography` with predicate (`region = 'EMEA'`).
  * Q13: Join with `dim_geography` with predicate (`region = 'North America'`).

### Category C: Advanced Analytical Queries (Q14–Q19)
* **Focus:** Advanced OLAP window functions, rankings, time-series calculations, and Top-K filters.
* **Schema Coverage:**
  * Q14: Window function: `RANK() OVER (ORDER BY SUM(gross_revenue) DESC)` joined with `dim_product`.
  * Q15: Cumulative running total: `SUM(SUM(gross_revenue)) OVER (ORDER BY t.calendar_month)` with `dim_time`.
  * Q16: Top-K sorting and truncation: `ORDER BY total_net_profit DESC LIMIT 3` joined with `dim_product`.
  * Q17: Time-series lag analysis: `LAG(SUM(gross_revenue)) OVER (ORDER BY t.calendar_month)` with `dim_time`.
  * Q18: Partitioned window function: `RANK() OVER (PARTITION BY p.category ORDER BY SUM(units_sold) DESC)`.
  * Q19: Ratio-to-report window computation: `ROUND((SUM(gross_revenue) * 100.0 / SUM(SUM(gross_revenue)) OVER ()), 2)`.

### Category D: Semantic / Schema Trap Queries (Q20–Q25)
* **Focus:** Testing LLM susceptibility to lexical ambiguity, column hallucination, and improper fact-table joins.
* **Trap Mechanisms:**
  * Q20 ("total revenue"): Traps the LLM into generating `revenue` instead of the actual schema column `gross_revenue`.
  * Q21 ("total discount"): Traps the LLM into generating `discount` instead of `discount_applied`.
  * Q22 ("total profit"): Traps the LLM into generating `profit` instead of `net_profit`.
  * Q23 ("average cost of products in each sub-category"): **Dimension-only query trap**. Tests if the LLM unnecessarily joins the 2,000-row fact table rather than querying `dim_product.unit_cost` directly.
  * Q24 ("revenue by market"): Traps the LLM into generating `market` instead of `market_type`.
  * Q25 ("profit and revenue by market type"): Combined trap requiring both `gross_revenue` and `net_profit` grouped by `market_type`.

---

## 7. Methodological Scope: Strengths and Limitations

### What This Synthetic Database Establishes
1. **Deterministic Reproducibility:** Fixed seed (seed=42) and explicit schema definitions guarantee bit-for-bit identical tables across any machine running PostgreSQL.
2. **Relational Equivalence Ground Truth:** Because the exact row population is known and static, generated SQL can be evaluated for execution accuracy against gold SQL by comparing exact returned relation tuples (with type normalization and unordered row comparisons).
3. **Controlled Repair Benchmarking:** The presence of known lexical trap queries (Category D) allows measuring how accurately the repair loop detects PostgreSQL runtime errors (e.g., `UndefinedColumn: column "revenue" does not exist`), generates `RuntimeKnowledge`, and admits governed repair memories to FAISS.
4. **Isolated Pipeline Evaluation:** Eliminates confounding network latency, dynamic enterprise transactions, and schema drift during agent benchmarking.

### What This Synthetic Database Cannot Establish
1. **Real-World Business Complexity:** The 8 products and 6 zones do not reflect real enterprise product hierarchies, multi-currency transactions, regional tax variations, or return/refund dynamics.
2. **Real Data Distributions & Demand Elasticity:** Units sold and markups are generated via independent uniform distributions; they do not exhibit real economic properties such as price elasticity (higher prices reducing demand) or seasonal holiday purchase spikes.
3. **Large-Scale Query Performance:** With 2,379 total rows, analytical queries execute in under 5 milliseconds. This cannot test PostgreSQL query plan optimization, partition pruning, parallel worker scans, or memory buffer starvation that occur on tables with millions or billions of rows.
4. **Data Hygiene & Nullability Challenges:** All columns are non-nullable and well-formatted. Real-world challenges such as missing values, corrupt timestamps, casing inconsistencies, and trailing whitespace are not present in this schema.

---

## 8. Provenance & Inference Documentation

* **Documented Fact:**
  - Table definitions, column types, check constraints, foreign keys, and indexes are taken verbatim from [`db/schema.sql`](file:///c:/Users/siddu/Pictures/armg%20main/db/schema.sql).
  - Seed=42, NumPy distributions, row counts (365, 6, 8, 2000), and financial formulas are verified verbatim from [`scripts/seed_warehouse.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/seed_warehouse.py).
  - The 25 queries and 4 categories are verified verbatim from [`benchmark/queries.json`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/queries.json).
* **Documented Rationale:**
  - Category D query design deliberately introduces terminology mismatch ("revenue", "discount", "profit") to test the repair loop's handling of PostgreSQL `UndefinedColumn` errors.
* **Methodological Inferences:**
  - The choice of 2,000 rows was selected as a tradeoff between sufficient analytical variety and sub-10ms execution latency for rapid 450-evaluation benchmarking.
* **Unknown Details:**
  - The original rationale for the specific unit costs (e.g., $80 for AI platform vs $500 for fiber switch) is not documented in comments; these are treated as arbitrary domain fixtures.
