# ARMG IEEE Literature Review & Scholarly Positioning

**Document Role**: Comprehensive Academic Literature Review & Theoretical Grounding  
**Target Manuscript**: `manuscript/ieee_manuscript.md`  
**Master Technical Baseline**: `ARMG_IEEE_Paper_Revision_Dossier.md` (Section 30)  
**Status**: Authoritative Literature Baseline — 100% Verified Citations  
**Date**: October 2026  

---

## 1. Search Methodology & Source Evaluation

To establish a defensible, peer-reviewed foundation for the Adaptive Runtime Memory Governance (ARMG) framework, we conducted external academic literature retrieval across leading venues in computer science, natural language processing, database systems, and AI security.

### Search Sources & Databases Consulted:
- **ACM Digital Library**: Symposium on User Interface Software and Technology (UIST), International Conference on Automated Software Engineering (ASE), Conference on Computer and Communications Security (CCS).
- **ACL Anthology**: Annual Meetings of the Association for Computational Linguistics (ACL), Empirical Methods in Natural Language Processing (EMNLP), International Conference on Computational Linguistics (COLING).
- **IEEE Xplore**: IEEE Transactions on Big Data (TBD), IEEE Transactions on Knowledge and Data Engineering (TKDE), IEEE International Conference on Data Engineering (ICDE).
- **Neural Information Processing Systems (NeurIPS)**: Main conference and Datasets & Benchmarks Track (2020–2023).
- **International Conference on Learning Representations (ICLR)** & **Transactions on Machine Learning Research (TMLR)** (2022–2024).
- **VLDB Endowment**: Proceedings of the VLDB Endowment (PVLDB 2024).
- **arXiv**: Verified author preprints and official technical reports for foundation models and open-source software frameworks (Qwen2.5, Nomic Embed, LangGraph, SQLGlot).

### Inclusion Criteria:
1. Peer-reviewed conference or journal publications from recognized venues (ACL, EMNLP, NeurIPS, ICLR, VLDB, IEEE, ACM) were prioritized for all theoretical, architectural, and methodological claims.
2. Official technical reports and software repositories were permitted strictly for foundational models (`qwen2.5:7b-instruct`, `nomic-embed-text`) and system orchestration frameworks (LangGraph, SQLGlot) where no traditional journal publication exists.
3. Every candidate reference was verified for exact title, author list, publication year, venue, and volume/pages or DOI/arXiv identifier.

---

## 2. Topic-by-Topic Literature Analysis

### Topic A: Modern LLM Text-to-SQL Architectures
- **DIN-SQL** (Pourreza & Rafiei, NeurIPS 2023): Decomposes Text-to-SQL into schema linking, query classification, SQL generation, and self-correction. Demonstrates that prompt decomposition enhances execution accuracy on Spider and BIRD.
  - *Relevance to ARMG*: Provides theoretical justification for multi-stage decomposition; ARMG extends this by moving from single-turn in-context repair to persistent runtime operational memory across queries.
- **DAIL-SQL** (Gao et al., PVLDB 2024): Conducts a systematic evaluation of prompt engineering across question representations, example selection, and organization, highlighting token efficiency in in-context learning.
  - *Relevance to ARMG*: Confirms the importance of prompt token efficiency and schema pruning. ARMG addresses token waste during iterative repair by injecting diagnostic negative constraints.
- **RAT-SQL** (Wang et al., ACL 2020): Introduced relation-aware schema encoding and schema linking using graph attention over tables and foreign keys.
  - *Relevance to ARMG*: Establishes historical foundational importance of explicit relational structure in semantic parsing.

### Topic B: Multi-Stage & Multi-Agent Collaborative Systems
- **MAC-SQL** (Wang et al., COLING 2025 / arXiv 2023): Implements a multi-agent framework utilizing specialized agents (Decomposer, Selector, Refiner) to handle Text-to-SQL tasks.
  - *Relevance to ARMG*: Represents the state of the art in agentic collaboration. However, MAC-SQL focuses on intra-query agent coordination without long-term operational memory governance across independent sequential queries.
- **C3** (Dong et al., arXiv 2023): A zero-shot Text-to-SQL framework using ChatGPT based on clear prompting, calibration with hints, and consistent output.
  - *Relevance to ARMG*: Shows that structured zero-shot prompting can achieve strong baseline results; highlights the need for bounded execution guardrails when moving beyond zero-shot.

### Topic C: LLM Self-Correction & Iterative Debugging
- **Self-Refine** (Madaan et al., NeurIPS 2023): Proposes iterative refinement where an LLM generates, critiques, and refines its output using verbal self-feedback without external execution.
  - *Relevance to ARMG*: Defines the conceptual baseline for verbal refinement; ARMG shows that for database systems, self-refinement must be grounded in physical database feedback rather than ungrounded internal self-critique.
- **Reflexion** (Shinn et al., NeurIPS 2023): Verbal reinforcement learning using episodic memory of self-reflections to improve future task iterations across coding and decision-making tasks.
  - *Relevance to ARMG*: Directly motivates verbal operational memory. However, Reflexion lacks mathematical admission control, multi-factor utility scoring, temporal decay, and mutual-exclusion deduplication.
- **Self-Debug** (Chen et al., ICLR 2024): Teaches LLMs to self-debug code by explaining execution traces and error messages via "rubber duck debugging" prompts.
  - *Relevance to ARMG*: Validates using execution error messages in repair prompts, which forms the operational basis of Mode 2 (Stateless Self-Correction).
- **Self-Edit** (Zhang et al., ACL 2023): Uses test-case execution results to edit code generation.
  - *Relevance to ARMG*: Emphasizes fault-aware prompting; ARMG formalizes this via deterministic 7-tier diagnosis and negative constraints.

### Topic D: Retrieval-Augmented Generation & Dense Vector Geometry
- **RAG** (Lewis et al., NeurIPS 2020): Foundational framework combining parametric memory (seq2seq models) with non-parametric memory (dense vector retrieval over Wikipedia).
  - *Relevance to ARMG*: Establishes the standard paradigm for external memory augmentation. ARMG addresses the critical flaw of naive RAG in database contexts: the unconstrained accumulation of redundant execution exemplars.
- **FAISS** (Johnson, Douze, & Jégou, IEEE Trans. Big Data 2021): High-performance library for dense vector similarity search, detailing GPU/CPU optimizations and Euclidean ($L_2$) distance computation.
  - *Relevance to ARMG*: Justifies the choice of `IndexFlatL2` and establishes the mathematical necessity of Unit-L2 normalization to bound Euclidean distances and preserve the $[0, 1]$ similarity threshold geometry.
- **Nomic Embed** (Nussbaum et al., arXiv 2024): Open-weights, reproducible text embedder with 8192-token context length and 768-dimensional representations.
  - *Relevance to ARMG*: Technical specification for the embedding model used across all benchmark modes.

### Topic E: LLM Memory Architectures & Cognitive Governance
- **Generative Agents** (Park et al., ACM UIST 2023): Formulates an agent memory stream with mathematical memory scoring based on recency, importance, and relevance, including exponential decay.
  - *Relevance to ARMG*: Provides the theoretical foundation for multi-factor memory utility and exponential decay equations. ARMG adapts these principles to structured database runtime knowledge.
- **MemGPT** (Packer et al., arXiv 2023): Proposes an operating-system-inspired hierarchical memory architecture (working context vs. archival storage) for bounded LLM context windows.
  - *Relevance to ARMG*: Emphasizes managing memory lifecycle; ARMG extends this by introducing deterministic admission gating and mutual exclusion between reinforcement and admission.
- **CoALA** (Sumers et al., TMLR 2024): A systematic cognitive architecture taxonomizing language agents along memory (working, episodic, semantic), action spaces, and decision procedures.
  - *Relevance to ARMG*: Situates ARMG within formal cognitive agent theory, classifying `RuntimeKnowledge` as working memory and `RuntimeMemory` as governed episodic storage.

### Topic F: Database Safety, Guardrails & AST Security
- **NeMo Guardrails** (Rebedea et al., EMNLP 2023 System Demonstrations): Open-source toolkit for programmable rails enforcing conversational boundaries and policy rules.
  - *Relevance to ARMG*: Illustrates the utility of external control layers; ARMG demonstrates that for relational databases, prompt-based rails must be replaced with deterministic AST parsing.
- **Jailbroken / Adversarial Attacks** (Wei et al., NeurIPS 2023; Zou et al., arXiv 2023): Proves that prompt-level safety alignment fails under adversarial prompt prefixes, suffixes, and semantic confusion.
  - *Relevance to ARMG*: Provides formal theoretical justification for why LLM prompt instructions alone cannot guarantee database safety, necessitating static AST-level containment.
- **AMNESIA** (Halfond & Orso, ACM/IEEE ASE 2005): Classic software engineering technique combining static analysis and runtime monitoring to neutralize SQL injection attacks by comparing queries against expected syntactic models.
  - *Relevance to ARMG*: Foundational precedent for deterministic syntactic model enforcement; ARMG modernizes this concept by parsing LLM-generated SQL queries via SQLGlot prior to execution.
- **SQLGlot** (Mao, GitHub / Software 2023): Python SQL parser, transpiler, and semantic analyzer supporting AST traversal across 30+ dialects.
  - *Relevance to ARMG*: The physical software implementation of ARMG's `ExecutionValidator` guardrail.

### Topic G: Text-to-SQL Benchmarking & Relational Equivalence
- **Spider Benchmark** (Yu et al., EMNLP 2018): Large-scale cross-domain benchmark comprising 10,181 questions across 200 databases.
  - *Relevance to ARMG*: Standard academic baseline for complex Text-to-SQL tasks.
- **BIRD Benchmark** (Li et al., NeurIPS 2023): Large-scale database benchmark containing 12,751 pairs over 95 dirty/noisy databases, highlighting the gap between execution success and human accuracy.
  - *Relevance to ARMG*: Demonstrates the real-world operational challenges of database values and the necessity of handling complex analytical SQL.
- **Evaluation Methodology** (Finegan-Dollak et al., ACL 2018): Identifies false-negative flaws in exact-string SQL matching, advocating for execution-based and denotational evaluation.
  - *Relevance to ARMG*: Theoretical justification for discarding string matching in favor of relational execution comparison.
- **Distilled Test Suites** (Zhong, Yu, & Klein, EMNLP 2020): Proposes test suite accuracy to approximate semantic equivalence by evaluating query execution results across diverse database instances.
  - *Relevance to ARMG*: Validates ARMG's `benchmark/equivalence.py` design, which evaluates multiset bag/set equivalence, row multiplicity, and numerical precision.
- **Execution-Guided Decoding** (Wang et al., arXiv 2018): Intercepts partial SQL generation during beam search, executing intermediate queries to filter out syntax and semantic errors.
  - *Relevance to ARMG*: Early precedent for execution-feedback-guided repair.

### Topic H: Model Scaling & Emergent Reasoning
- **Emergent Abilities** (Wei et al., TMLR 2022): Documents that complex multi-step reasoning capabilities emerge at specific parameter and compute scale thresholds.
  - *Relevance to ARMG*: Contextualizes the 68.00% relational semantic plateau: 7B-parameter models exhibit inherent capacity boundaries on nested window functions (`RANK() OVER`, `PARTITION BY`, `LAG()`) that external operational memory cannot bridge.

---

## 3. Systematic Research Gap Synthesis

A forensic review of the literature reveals a clear, unaddressed research gap:

```
+---------------------------------------------------------------------------------------------------+
| PRIOR WORK FOCUS                                                                                  |
+---------------------------------------------------------------------------------------------------+
| 1. Advanced Prompting & Decomposition: DIN-SQL, DAIL-SQL, MAC-SQL                                 |
|    -> Focus exclusively on in-context prompt optimization for cloud-scale frontier models.        |
|    -> Do not address runtime cross-query operational memory or local deployment memory bloat.     |
|                                                                                                   |
| 2. Stateless Self-Correction: Self-Refine, Reflexion, Self-Debug                                  |
|    -> Prompts model with raw error traces within an isolated query attempt.                       |
|    -> Memoryless across queries; prone to repetitive repair cycling and prompt token overhead.    |
|                                                                                                   |
| 3. Unmanaged Vector RAG: Standard dense vector stores (FAISS, LangChain)                          |
|    -> Appends raw (question, sql) exemplars upon execution success.                               |
|    -> Lacks admission gating, mathematical utility decay, and deduplication controls.             |
|                                                                                                   |
| 4. Prompt-Based Safety Rails: NeMo Guardrails, system prompt instructions                         |
|    -> Probabilistic, vulnerable to jailbreaks, hallucinations, and destructive DDL/DML mutations. |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| THE UNADDRESSED RESEARCH GAP                                                                      |
+---------------------------------------------------------------------------------------------------+
| How to design an integrated, closed-loop runtime architecture for local, open-weights Text-to-SQL |
| systems that:                                                                                     |
| (a) Intercepts physical database errors and classifies them into a code-first deterministic       |
|     exception taxonomy without LLM token expenditure;                                             |
| (b) Injects diagnostic negative constraints to prevent repair oscillation;                        |
| (c) Governs the persistent vector lifecycle through admission gating and mutual-exclusion         |
|     deduplication; and                                                                            |
| (d) Enforces deterministic pre-execution AST safety boundaries,                                   |
| while rigorously measuring the operational trade-offs across repair efficiency, token economy,    |
| latency overhead, and the relational semantic accuracy ceiling of 7B-parameter models.            |
+---------------------------------------------------------------------------------------------------+
```

ARMG is explicitly positioned to investigate this integrated runtime operational governance gap.
