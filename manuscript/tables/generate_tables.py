"""
Generates all 9 camera-ready LaTeX table files for IEEE formatting.
Corrected in Step 5.1:
- Table V: Canonical 6/8/2000 schema with time_key, geo_key, product_key, fact_key.
- Table VI: Canonical 5/8/6/6 query corpus distribution (Q01-Q05, Q06-Q13, Q14-Q19, Q20-Q25).
- Table VIII: Non-causal descriptive interpretation for relational semantic accuracy.
- Sanitized LaTeX syntax without embedded markdown or unescaped underscores.
"""
import os

def generate_tables():
    os.makedirs('manuscript/tables', exist_ok=True)
    
    # =========================================================================
    # Table I: Canonical 7-Tier Exception Taxonomy Matrix
    # =========================================================================
    t1_tex = r"""\begin{table*}[t]
\centering
\caption{Canonical 7-Tier Exception Taxonomy Matrix and Candidate Repair Heuristics}
\label{tab:taxonomy}
\begin{tabular}{ccllp{5.5cm}}
\hline
\textbf{Tier} & \textbf{Category} & \textbf{Implementation Definition} & \textbf{Detection Pattern / Trigger} & \textbf{Candidate Repair Action} \\
\hline
1 & Validation & Syntactic/Safety AST rejections & Non-SELECT, destructive DDL/DML, stacked injections & Abort repair loop; transition to \texttt{STATUS\_BLOCKED} \\
2 & Syntax & Malformed SQL syntax & Driver syntax errors, unclosed quotes, malformed clauses & Strip invalid tokens; regenerate with strict SQL grammar \\
3 & Semantic & Schema/Identifier non-existence & Unknown column/table names, column ambiguity & Remap to closest catalog token; inject negative constraint \\
4 & Planning & Cartesian products / Join failures & Unbounded joins, missing foreign-key predicates & Inject explicit \texttt{JOIN ... ON} clause from schema catalog \\
5 & Permission & Privileged/Administrative commands & Read-only violations, grant/revoke rejections & Block execution; restrict to read-only \texttt{SELECT} \\
6 & Resource & Operational execution timeouts & Query cancellation, memory quota exceeded & Enforce query timeout; suggest predicate pushdown \\
7 & Execution & Unclassified runtime driver failures & Catch-all database exceptions & Fallback to raw normalized driver error trace \\
\hline
\end{tabular}
\end{table*}
"""
    with open('manuscript/tables/table1_taxonomy.tex', 'w', encoding='utf-8') as f:
        f.write(t1_tex.strip() + '\n')

    # =========================================================================
    # Table II: Comparative Empirical Benchmark Results Across Six Modes
    # =========================================================================
    t2_tex = r"""\begin{table*}[t]
\centering
\caption{Comparative Empirical Benchmark Results Across Six Experimental Modes ($n = 3$ Repeated Executions)}
\label{tab:results}
\begin{tabular}{lcccccc}
\hline
\textbf{Experimental Mode} & \textbf{ExecAcc (\%)} & \textbf{ExecSucc (\%)} & \textbf{Retries ($K$)} & \textbf{Latency (ms)} & \textbf{Tokens} & \textbf{Store Size} \\
\hline
Mode 1 (Zero-Shot) & $57.33 \pm 2.31$ & $76.00 \pm 0.00$ & $0.00 \pm 0.00$ & $5,087.73 \pm 210.33$ & $360.48 \pm 0.48$ & $0$ \\
Mode 2 (Stateless Self-Correction) & $68.00 \pm 0.00$ & $92.00 \pm 0.00$ & $0.43 \pm 0.02$ & $7,149.68 \pm 231.65$ & $572.72 \pm 12.68$ & $0$ \\
Mode 3 (Naive Vector RAG) & $68.00 \pm 0.00$ & $92.00 \pm 0.00$ & $0.00 \pm 0.00$ & $6,844.01 \pm 56.90$ & $558.28 \pm 0.00$ & $23$ \\
Mode 4 (Full ARMG) & $68.00 \pm 0.00$ & $96.00 \pm 0.00$ & $0.28 \pm 0.00$ & $8,564.89 \pm 103.16$ & $542.37 \pm 0.02$ & $3$ \\
Mode 5 (ARMG $-$ Neg Constraints) & $68.00 \pm 0.00$ & $96.00 \pm 0.00$ & $0.36 \pm 0.00$ & $8,941.28 \pm 108.68$ & $553.93 \pm 0.02$ & $3$ \\
Mode 6 (ARMG with $\lambda = 0.0$) & $68.00 \pm 0.00$ & $94.67 \pm 2.31$ & $0.37 \pm 0.02$ & $9,036.97 \pm 178.55$ & $599.67 \pm 13.94$ & $3$ \\
\hline
\multicolumn{7}{l}{\footnotesize \textsuperscript{*}All reported figures represent mean $\pm$ sample standard deviation across three repeated executions under seeds 42, 123, and 999.} \\
\end{tabular}
\end{table*}
"""
    with open('manuscript/tables/table2_results.tex', 'w', encoding='utf-8') as f:
        f.write(t2_tex.strip() + '\n')

    # =========================================================================
    # Table III: PostgreSQL Execution Success vs. Relational Semantic Accuracy
    # =========================================================================
    t3_tex = r"""\begin{table}[h]
\centering
\caption{PostgreSQL Execution Success vs. Relational Semantic Accuracy Across All Six Modes}
\label{tab:gap}
\begin{tabular}{lccc}
\hline
\textbf{Experimental Mode} & \textbf{ExecSucc (\%)} & \textbf{ExecAcc (\%)} & \textbf{Discrepancy Gap (pp)} \\
\hline
Mode 1 (Zero-Shot) & 76.00 & 57.33 & 18.67 \\
Mode 2 (Stateless Self-Correction) & 92.00 & 68.00 & 24.00 \\
Mode 3 (Naive Vector RAG) & 92.00 & 68.00 & 24.00 \\
Mode 4 (Full ARMG) & 96.00 & 68.00 & 28.00 \\
Mode 5 (ARMG $-$ Neg Constraints) & 96.00 & 68.00 & 28.00 \\
Mode 6 (ARMG with $\lambda = 0.0$) & 94.67 & 68.00 & 26.67 \\
\hline
\multicolumn{4}{l}{\footnotesize Discrepancy Gap defined as $\text{ExecSucc} - \text{ExecAcc}$ in percentage points (pp).} \\
\end{tabular}
\end{table}
"""
    with open('manuscript/tables/table3_gap.tex', 'w', encoding='utf-8') as f:
        f.write(t3_tex.strip() + '\n')

    # =========================================================================
    # Table IV: Canonical System Configuration and Component Mapping
    # =========================================================================
    t4_tex = r"""\begin{table}[h]
\centering
\caption{Canonical System Configuration and Component Mapping}
\label{tab:system_config}
\begin{tabular}{lll}
\hline
\textbf{Subsystem / Component} & \textbf{Implementation Anchor} & \textbf{Version / Operational Specification} \\
\hline
Foundation Model & Local Ollama instance & \texttt{qwen2.5:7b-instruct} (7.61B parameters) \\
Inference Configuration & Greedy decoding & \texttt{temperature = 0.0}, \texttt{top\_p = 1.0} \\
Embedding Model & Local Ollama instance & \texttt{nomic-embed-text} (768d, Unit-$L_2$ normalized) \\
Vector Indexing Library & CPU Flat Index & FAISS \texttt{IndexIDMap2} wrapping \texttt{IndexFlatL2} \\
Relational Data Warehouse & Physical container & PostgreSQL 16.2 on \texttt{localhost:5432} \\
Graph Orchestration & Directed state graph & LangGraph 0.2.x (\texttt{StateGraph} runtime) \\
Static SQL Parser & AST guardrail & SQLGlot 25.x (Dialect: PostgreSQL) \\
Execution Driver & Python DB-API 2.0 & \texttt{psycopg2-binary} 2.9.x \\
Python Runtime Environment & Local Workstation & Python 3.11.9 (NVIDIA CUDA acceleration via Ollama) \\
\hline
\end{tabular}
\end{table}
"""
    with open('manuscript/tables/table4_config.tex', 'w', encoding='utf-8') as f:
        f.write(t4_tex.strip() + '\n')

    # =========================================================================
    # Table V: Relational Data Warehouse Star Schema Specification (Corrected)
    # =========================================================================
    t5_tex = r"""\begin{table}[h]
\centering
\caption{Relational Data Warehouse Star Schema Specification}
\label{tab:schema}
\begin{tabular}{lcllp{4.5cm}}
\hline
\textbf{Table Name} & \textbf{Role} & \textbf{Rows} & \textbf{Primary Key} & \textbf{Major Attributes / Foreign Key Constraints} \\
\hline
\texttt{dim\_time} & Dimension & 365 & \texttt{time\_key} & full\_date, day\_of\_week, calendar\_month, calendar\_quarter, calendar\_year \\
\texttt{dim\_geography} & Dimension & 6 & \texttt{geo\_key} & region, zone, market\_type \\
\texttt{dim\_product} & Dimension & 8 & \texttt{product\_key} & product\_name, category, sub\_category, unit\_cost \\
\texttt{fact\_sales\_performance} & Fact & 2,000 & \texttt{fact\_key} & units\_sold, gross\_revenue, discount\_applied, net\_profit. \newline FK: \texttt{time\_key}, \texttt{geo\_key}, \texttt{product\_key} \\
\hline
\multicolumn{5}{l}{\footnotesize \textsuperscript{*}Deterministically seeded via NumPy \texttt{seed=42} (\texttt{scripts/seed\_warehouse.py}).} \\
\end{tabular}
\end{table}
"""
    with open('manuscript/tables/table5_schema.tex', 'w', encoding='utf-8') as f:
        f.write(t5_tex.strip() + '\n')

    # =========================================================================
    # Table VI: Benchmark Query Corpus Distribution (Corrected)
    # =========================================================================
    t6_tex = r"""\begin{table}[h]
\centering
\caption{Benchmark Query Corpus Distribution Across Complexity Categories}
\label{tab:query_corpus}
\begin{tabular}{lccl}
\hline
\textbf{Category} & \textbf{Queries} & \textbf{Count} & \textbf{Analytical Focus and SQL Clause Complexity} \\
\hline
Category A & Q01--Q05 & 5 & Simple aggregations, basic filters, group-by, order-by clauses \\
Category B & Q06--Q13 & 8 & Multi-table Star Schema joins, dimension filtering, compound conditions \\
Category C & Q14--Q19 & 6 & Advanced window functions (\texttt{RANK()}, \texttt{LAG()}, cumulative partitions) \\
Category D & Q20--Q25 & 6 & Semantic/schema trap queries, attribute sequence inversions, strict ordering \\
\hline
\textbf{Total Corpus} & Q01--Q25 & 25 & B2B Technology Sales Analytics Domain (\texttt{benchmark/queries.json}) \\
\hline
\end{tabular}
\end{table}
"""
    with open('manuscript/tables/table6_queries.tex', 'w', encoding='utf-8') as f:
        f.write(t6_tex.strip() + '\n')

    # =========================================================================
    # Table VII: Mathematical Governance Control Equations
    # =========================================================================
    t7_tex = r"""\begin{table*}[t]
\centering
\caption{Mathematical Governance Engine Control Equations and Parameter Specifications}
\label{tab:governance_equations}
\begin{tabular}{lllp{4.5cm}}
\hline
\textbf{Control Mechanism} & \textbf{Formal Equation / Formulation} & \textbf{Parameter Defaults} & \textbf{Operational Implementation Role} \\
\hline
Operational Utility & $\text{Utility} = C \times \text{SuccessRate} \times \text{ContextSim} \times \text{Recency}$ & Priors: $C_0=0.5, \text{SR}_0=0.5$ & Multi-factor utility evaluation \\
Admission Gating & $\text{Admit}(K) \iff \text{Utility}_0(K) \ge \theta_{\text{admit}}$ & $\theta_{\text{admit}} = 0.25$ & Gating candidate operational knowledge \\
Confidence Escalation & $C_{t+1} = C_t + \alpha (1.0 - C_t)$ & $\alpha = 0.10$ & Asymptotic reinforcement upon success \\
Failure Penalty & $C_{t+1} = \max(0.0, \, C_t \times (1.0 - \beta))$ & $\beta = 0.15$ & Multiplicative confidence penalty on failure \\
Continuous Decay & $C(t) = C_{\text{ref}} \times \exp(-\lambda \Delta t)$ & $\lambda = 0.05\text{ day}^{-1}$ & Exponential decay over time ($*$Unexercised) \\
Mutual Exclusion & $\text{Reinforce}(M) \iff M_{\text{applied}} \neq \emptyset$; $\text{Admit}(K)$ otherwise & Mutually exclusive & Invariant preventing duplicate memory bloat \\
\hline
\multicolumn{4}{l}{\footnotesize \textsuperscript{*}Temporal decay is fully unit-tested in \texttt{tests/unit/test\_governance.py}, but unexercised under the 3.5-minute benchmark execution clock.} \\
\end{tabular}
\end{table*}
"""
    with open('manuscript/tables/table7_governance.tex', 'w', encoding='utf-8') as f:
        f.write(t7_tex.strip() + '\n')

    # =========================================================================
    # Table VIII: Mode 4 vs. Mode 2 Comparative Trade-Off Analysis (Corrected)
    # =========================================================================
    t8_tex = r"""\begin{table*}[t]
\centering
\caption{Mode 4 (Full ARMG) vs. Mode 2 (Stateless Self-Correction) Comparative Trade-Off Profile}
\label{tab:tradeoff}
\begin{tabular}{lrrccp{5.5cm}}
\hline
\textbf{Evaluation Dimension} & \textbf{Mode 2} & \textbf{Mode 4} & \textbf{Absolute Delta} & \textbf{Relative Delta} & \textbf{Operational Engineering Interpretation} \\
\hline
Mean Repair Retries ($K$) & 0.43 & 0.28 & $-0.15$ retries & $-34.38\%$ & Observed reduction in repair iterations \\
Mean Token Expenditure & 572.72 & 542.37 & $-30.35$ tokens & $-5.30\%$ & Token savings by avoiding repetitive repair prompts \\
PostgreSQL Execution Success & $92.00\%$ & $96.00\%$ & $+4.00\text{ pp}$ & $+4.35\%$ & Execution recovery on Query Q19 \\
End-to-End Latency & $7,149.68\text{ ms}$ & $8,564.89\text{ ms}$ & $+1,415.21\text{ ms}$ & $+19.79\%$ & Architectural overhead of state graph and FAISS \\
Relational Semantic Accuracy & $68.00\%$ & $68.00\%$ & $0.00\text{ pp}$ & $0.00\%$ & Observed identical relational execution accuracy in the evaluated benchmark \\
\hline
\multicolumn{6}{l}{\footnotesize \textsuperscript{*}Percentage points (pp) and relative percentage changes (\%) are strictly distinguished.} \\
\end{tabular}
\end{table*}
"""
    with open('manuscript/tables/table8_tradeoff.tex', 'w', encoding='utf-8') as f:
        f.write(t8_tex.strip() + '\n')

    # =========================================================================
    # Table IX: Forensic Diagnostic Breakdown of Seven Divergent Semantic Queries
    # =========================================================================
    t9_tex = r"""\begin{table*}[t]
\centering
\caption{Forensic Diagnostic Breakdown of the Seven Divergent Semantic Queries in Mode 4}
\label{tab:divergent_queries}
\begin{tabular}{ccclp{4.8cm}p{4.2cm}}
\hline
\textbf{Query} & \textbf{Cat} & \textbf{PG Status} & \textbf{RelAcc} & \textbf{Generated SQL Construct Deviation} & \textbf{Comparator Diagnostic Rationale} \\
\hline
Q05 & A & Success & False & Omitted required \texttt{ORDER BY net\_profit DESC} & Gold required ordering; positional sequence matching failed \\
Q14 & C & Success & False & Substituted simple \texttt{ORDER BY} for \texttt{RANK() OVER} & Failed multiset row ranking equivalence \\
Q15 & C & Success & False & Computed monthly aggregation without cumulative frame & Omitted running total window specification \\
Q17 & C & Success & False & Included invalid grouping attribute in \texttt{LAG()} partition & Generated multi-row monthly output instead of scalar lag \\
Q18 & C & Success & False & Ranked globally without \texttt{PARTITION BY category} & Missed category-scoped partition grouping \\
Q19 & C & Success & False & Omitted base revenue column and rounding format & Projection signature and decimal precision discrepancy \\
Q25 & D & Success & False & Inverted column sequence: \texttt{(market, profit, rev)} & Positional tuple attribute mismatch against gold signature \\
\hline
\multicolumn{6}{l}{\footnotesize \textsuperscript{*}Q05 executed cleanly on PostgreSQL but failed because the comparator enforces strict positional matching when gold SQL specifies ordering.} \\
\end{tabular}
\end{table*}
"""
    with open('manuscript/tables/table9_failures.tex', 'w', encoding='utf-8') as f:
        f.write(t9_tex.strip() + '\n')

    print("All 9 LaTeX tables generated successfully in manuscript/tables/ with canonical corrections.")

if __name__ == '__main__':
    generate_tables()
