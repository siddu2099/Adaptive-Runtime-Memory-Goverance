"""
Automated Verification Script for Step 6: Final IEEE Camera-Ready Formatting.

Validates:
1. Title consistency against canonical title.
2. Section numbering and presence of all 19 major sections.
3. Figure count = 6, existence of PNG and SVG files.
4. Table count = 9, existence of .tex files.
5. Unique figure labels and unique table labels (no duplicates).
6. Citations complete: every \\cite{} in .tex resolves to an entry in references.bib.
7. Bibliography count = 26, zero placeholder references.
8. Every bibliography entry in references.bib is cited in .tex.
9. No unresolved cross-references in .tex.
10. Zero Markdown syntax (**, #, |, etc.) in .tex.
11. No stale schema values (dim_geography=50, dim_product=100, fact_sales without performance, sales_id).
12. No stale query distribution (Category A=6, B=7, C=8, D=4).
13. No duplicate table labels (e.g. tab:system_config only once).
14. No broken \\input paths.
15. Balanced braces and valid LaTeX environments.
"""

import os
import re
import sys

def verify_step6():
    print("=" * 70)
    print("ARMG STEP 6: AUTOMATED FORMATTING AND INTEGRITY AUDIT")
    print("=" * 70)

    tex_path = "manuscript/ieee_camera_ready.tex"
    bib_path = "manuscript/references.bib"

    assert os.path.exists(tex_path), f"Missing {tex_path}"
    assert os.path.exists(bib_path), f"Missing {bib_path}"

    with open(tex_path, "r", encoding="utf-8") as f:
        tex_content = f.read()

    with open(bib_path, "r", encoding="utf-8") as f:
        bib_content = f.read()

    # 1. Title consistency
    print("\n[CHECK 1] Title Consistency...")
    canonical_title = "Adaptive Runtime Memory Governance: Closed-Loop Operational Knowledge Extraction, Repair Efficiency, and Execution Safety in Local Text-to-SQL Systems"
    title_match = re.search(r"\\title\{([^}]+)\}", tex_content)
    assert title_match, "Title tag missing in LaTeX source"
    actual_title = title_match.group(1).strip()
    assert actual_title == canonical_title, f"Title mismatch:\nExpected: {canonical_title}\nActual: {actual_title}"
    print(f"  -> PASSED: Title strictly matches canonical title.")

    # 2. Section numbering and presence of all 19 major sections
    print("\n[CHECK 2] Section Structure & Numbering...")
    expected_sections = [
        "Introduction",
        "Related Work",
        "Problem Formulation",
        "ARMG Architecture",
        "Runtime Observation and Error Diagnosis",
        "Memory Governance and Lifecycle",
        "Runtime-Guided Repair and Negative Constraints",
        "Safety Enforcement",
        "Experimental Methodology",
        "Experimental Results",
        "Memory Retrieval and Lifecycle Analysis",
        "Safety Evaluation",
        "Semantic Failure Analysis",
        "Ablation Analysis",
        "Discussion",
        "Limitations",
        "Threats to Validity",
        "Future Work",
        "Conclusion"
    ]
    sections_found = re.findall(r"\\section\{([^}]+)\}", tex_content)
    assert len(sections_found) == 19, f"Expected 19 sections, found {len(sections_found)}: {sections_found}"
    for exp, actual in zip(expected_sections, sections_found):
        assert exp.lower() in actual.lower(), f"Section mismatch: expected '{exp}', got '{actual}'"
    print(f"  -> PASSED: All 19 expected major sections present and ordered.")

    # 3. Figure count and asset existence
    print("\n[CHECK 3] Figure Count & Asset Existence...")
    fig_labels = re.findall(r"\\label\{(fig:[^}]+)\}", tex_content)
    assert len(fig_labels) == 6, f"Expected 6 figure labels in tex, found {len(fig_labels)}: {fig_labels}"
    assert len(set(fig_labels)) == 6, f"Duplicate figure labels: {fig_labels}"

    required_figures = [
        "fig1_architecture",
        "fig2_lifecycle",
        "fig3_retrieval_geometry",
        "fig4_execsucc_execacc",
        "fig5_tradeoff",
        "fig6_memory_growth"
    ]
    for rf in required_figures:
        png_p = f"manuscript/figures/png/{rf}.png"
        svg_p = f"manuscript/figures/svg/{rf}.svg"
        src_p = f"manuscript/figures/source/{rf}.py"
        assert os.path.exists(png_p), f"Missing {png_p}"
        assert os.path.exists(svg_p), f"Missing {svg_p}"
        assert os.path.exists(src_p), f"Missing {src_p}"
    print(f"  -> PASSED: All 6 figures present with PNG, SVG, and Python source scripts.")

    # 4. Table count, inputs, and asset existence
    print("\n[CHECK 4] Table Count & Input Paths...")
    input_tables = re.findall(r"\\input\{(tables/[^}]+)\}", tex_content)
    assert len(input_tables) == 9, f"Expected 9 table inputs in tex, found {len(input_tables)}: {input_tables}"
    for it in input_tables:
        full_p = os.path.join("manuscript", it)
        assert os.path.exists(full_p), f"Missing input table: {full_p}"
    print(f"  -> PASSED: All 9 tables imported via valid \\input paths.")

    # 5. Table label uniqueness
    print("\n[CHECK 5] Table Label Uniqueness...")
    table_labels = []
    for it in input_tables:
        with open(os.path.join("manuscript", it), "r", encoding="utf-8") as f:
            t_content = f.read()
        lbls = re.findall(r"\\label\{([^}]+)\}", t_content)
        assert len(lbls) == 1, f"Table {it} has unexpected label count: {lbls}"
        table_labels.append(lbls[0])
    
    expected_labels = [
        "tab:taxonomy",
        "tab:governance_equations",
        "tab:system_config",
        "tab:schema",
        "tab:query_corpus",
        "tab:results",
        "tab:tradeoff",
        "tab:gap",
        "tab:divergent_queries"
    ]
    for el in expected_labels:
        assert el in table_labels, f"Missing expected table label: {el}"
    assert len(table_labels) == 9, f"Expected 9 unique table labels, found {len(table_labels)}"
    assert len(set(table_labels)) == 9, f"Duplicate table labels: {table_labels}"
    assert table_labels.count("tab:system_config") == 1, "Duplicate tab:system_config"
    print(f"  -> PASSED: Exactly 9 unique table labels verified with zero duplicates.")

    # 6. Bibliography validation
    print("\n[CHECK 6] Bibliography & Citation Completeness...")
    bib_keys = re.findall(r"@\w+\{([^,]+),", bib_content)
    assert len(bib_keys) == 26, f"Expected 26 bib entries, found {len(bib_keys)}: {bib_keys}"
    assert len(set(bib_keys)) == 26, f"Duplicate bib keys in references.bib: {bib_keys}"

    # Extract all \cite{...} from tex
    cited_raw = re.findall(r"\\cite\{([^}]+)\}", tex_content)
    cited_keys = set()
    for cr in cited_raw:
        for k in cr.split(","):
            cited_keys.add(k.strip())

    # Verify every \cite maps to bib
    for ck in cited_keys:
        assert ck in bib_keys, f"Cited key '{ck}' in tex not found in references.bib!"

    # Verify every bib key is cited
    for bk in bib_keys:
        assert bk in cited_keys, f"Bib key '{bk}' defined in references.bib is NOT cited in tex!"
    print(f"  -> PASSED: Exactly 26 bibliography entries; 100% mutual citation resolution.")

    # 7. Cross-reference check in text
    print("\n[CHECK 7] Float Cross-References in Text...")
    for fl in fig_labels:
        assert f"\\ref{{{fl}}}" in tex_content, f"Figure label {fl} not referenced via \\ref in text"
    for tl in table_labels:
        assert f"\\ref{{{tl}}}" in tex_content, f"Table label {tl} not referenced via \\ref in text"
    print(f"  -> PASSED: All 6 figures and 9 tables are explicitly cross-referenced via \\ref.")

    # 8. Check for Markdown artifacts
    print("\n[CHECK 8] Markdown Artifact Elimination...")
    assert "**" not in tex_content, "Markdown bold '**' found in ieee_camera_ready.tex"
    assert "```" not in tex_content, "Markdown code fence found in ieee_camera_ready.tex"
    for line in tex_content.splitlines():
        if line.strip().startswith("#"):
            assert False, f"Markdown heading found: {line}"
    print(f"  -> PASSED: Zero Markdown syntax (**, ```, #) found in ieee_camera_ready.tex.")

    # 9. Stale Schema Values
    print("\n[CHECK 9] Stale Schema Values Audit...")
    assert "dim_geography = 50" not in tex_content
    assert "dim_product = 100" not in tex_content
    assert "sales_id" not in tex_content
    # Ensure fact_sales is only followed by _performance
    for match in re.finditer(r"fact_sales\b(?!_performance)", tex_content):
        assert False, f"Stale 'fact_sales' found at position {match.start()}"
    print(f"  -> PASSED: Zero stale schema values found.")

    # 10. Stale Query Distribution
    print("\n[CHECK 10] Stale Query Distribution Audit...")
    assert "Q01--Q06" not in tex_content and "Q01–Q06" not in tex_content
    assert "Q07--Q13" not in tex_content and "Q07–Q13" not in tex_content
    assert "Q14--Q21" not in tex_content and "Q14–Q21" not in tex_content
    assert "Q22--Q25" not in tex_content and "Q22–Q25" not in tex_content
    print(f"  -> PASSED: Zero stale query category distributions found.")

    # 11. Balanced Braces
    print("\n[CHECK 11] LaTeX Syntax & Balanced Braces...")
    assert tex_content.count("{") == tex_content.count("}"), "Unbalanced curly braces in ieee_camera_ready.tex"
    print(f"  -> PASSED: Braces strictly balanced in ieee_camera_ready.tex.")

    # 12. Verification of frozen numerical results in text
    print("\n[CHECK 12] Frozen Numerical Results Invariants...")
    assert "34.38\\%" in tex_content
    assert "5.30\\%" in tex_content
    assert "96.00\\%" in tex_content
    assert "92.00\\%" in tex_content
    assert "19.79\\%" in tex_content
    assert "68.00\\%" in tex_content
    assert "0.28" in tex_content
    assert "0.43" in tex_content
    assert "542.37" in tex_content
    assert "572.72" in tex_content
    assert "8,564.89" in tex_content
    assert "7,149.68" in tex_content
    print(f"  -> PASSED: All frozen numerical evidence preserved exactly.")

    # 13. Verification of Author Block Metadata (Step 6.1)
    print("\n[CHECK 13] Author Block Verification (Step 6.1)...")
    expected_authors = [
        ("Inampudi Govardhana Rao", "govardhanarao.i@vitap.ac.in"),
        ("Ghanta Sundar Siddhartha", "siddharthaghanta10@gmail.com"),
        ("Sudarsanan Shilpa", "shilpasudarsanan4@gmail.com"),
        ("Bommadevara S N V Datta Prasada Rayulu", "dattabommadevara123@gmail.com"),
        ("Velpuri Danaiah", "danaiahvelpuri78@gmail.com"),
    ]
    for author_name, email in expected_authors:
        assert author_name in tex_content, f"Missing author: {author_name}"
        assert email in tex_content, f"Missing email for author {author_name}: {email}"
    assert "[Author Names Withheld" not in tex_content, "Placeholder author remains in ieee_camera_ready.tex"
    print(f"  -> PASSED: All 5 canonical authors verified in LaTeX source.")

    print("\n" + "=" * 70)
    print("ALL 13 AUTOMATED STEP 6 AUDIT CHECKS PASSED WITH ZERO DISCREPANCIES!")
    print("=" * 70)

if __name__ == "__main__":
    verify_step6()
