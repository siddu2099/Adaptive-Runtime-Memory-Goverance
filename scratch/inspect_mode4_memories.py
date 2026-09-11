import csv
import sys
from pathlib import Path
repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
sys.path.insert(0, str(repo_root))
from agents.schema_introspector import SchemaIntrospector
from agents.schema_pruner import SchemaPruner
from agents.sql_generator import SQLGenerator
from agents.repair_agent import RepairSQLGenerator
from environment.postgres import PostgreSQLEnvironment
from graph.workflow import ARMGRepairWorkflow, default_embed_fn
from memory.vector_store import FAISSMemoryStore
from validation.execution_validator import ExecutionValidator
from benchmark.modes import execute_mode_4_full_armg
from scripts.eval_runner import load_and_validate_dataset

# Let's inspect the questions for Q04, Q13, Q15, Q17 and see their wording and text
dataset = load_and_validate_dataset()
q_by_id = {item["query_id"]: item for item in dataset}

print("=== ADMISSION QUERIES IN MODE 4 ===")
for qid in ["Q04", "Q13", "Q15", "Q17"]:
    item = q_by_id[qid]
    print(f"{qid}: ({item['category']})")
    print(f"  Question: {item['question']}")
    print(f"  Gold SQL: {item['gold_sql']}")

print("\n=== RETRIEVAL QUERIES IN MODE 4 ===")
for qid in ["Q08", "Q10", "Q16", "Q17", "Q18", "Q19", "Q20", "Q21", "Q22", "Q23", "Q24", "Q25"]:
    item = q_by_id[qid]
    print(f"{qid}: ({item['category']})")
    print(f"  Question: {item['question']}")
