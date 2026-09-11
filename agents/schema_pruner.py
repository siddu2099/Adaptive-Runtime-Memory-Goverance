"""
ARMG Phase 2: Deterministic Schema Pruner.

Implements rule-based, deterministic table selection based on user question keywords.
Does NOT use LLMs or semantic embeddings, ensuring fast zero-cost pruning.
"""

import re
from typing import List, Set


# Keyword rules for Star Schema dimension tables
TIME_KEYWORDS = {
    "time", "date", "year", "month", "quarter", "day", "period",
    "annual", "daily", "monthly", "quarterly", "weekly",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "2024", "2025", "2026",
}

GEOGRAPHY_KEYWORDS = {
    "region", "zone", "geography", "geographic", "market", "location", "country",
    "emea", "apac", "north america",
}

PRODUCT_KEYWORDS = {
    "product", "category", "sub-category", "subcategory", "item", "unit cost",
}

FACT_TABLE = "fact_sales_performance"
ALL_TABLES = ["dim_time", "dim_geography", "dim_product", "fact_sales_performance"]


def prune_schema_tables(question: str) -> List[str]:
    """Deterministically select relevant schema tables for a given user query.
    
    Rules:
    - Always include fact_sales_performance.
    - If question references time/date keywords, include dim_time.
    - If question references geography/region/location keywords, include dim_geography.
    - If question references product/category keywords, include dim_product.
    - If no specific dimension keywords match, return all 4 tables (ambiguous query fallback).
    
    Args:
        question: Natural language user question string.
        
    Returns:
        List of selected table names in deterministic sorted order.
    """
    if not question or not question.strip():
        return sorted(ALL_TABLES)

    text_lower = question.lower()
    # Normalize hyphens for compound words like sub-category
    tokens = set(re.findall(r"\b[\w-]+\b", text_lower))

    selected: Set[str] = {FACT_TABLE}
    matched_any_dimension = False

    # Check Time keywords
    if any(k in tokens or k in text_lower for k in TIME_KEYWORDS):
        selected.add("dim_time")
        matched_any_dimension = True

    # Check Geography keywords
    if any(k in tokens or k in text_lower for k in GEOGRAPHY_KEYWORDS):
        selected.add("dim_geography")
        matched_any_dimension = True

    # Check Product keywords
    if any(k in tokens or k in text_lower for k in PRODUCT_KEYWORDS):
        selected.add("dim_product")
        matched_any_dimension = True

    # If only fact table selected and no dimension keywords matched, fall back to all tables
    if not matched_any_dimension:
        return sorted(ALL_TABLES)

    return sorted(list(selected))


class SchemaPruner:
    """Class wrapper for deterministic schema pruning."""

    @staticmethod
    def prune(question: str) -> List[str]:
        """Prune tables for question."""
        return prune_schema_tables(question)
