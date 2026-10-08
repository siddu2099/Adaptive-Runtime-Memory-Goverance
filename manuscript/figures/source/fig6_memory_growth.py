"""
Figure 6: Persistent Memory Store Growth: Full ARMG vs. Naive Vector RAG
Step plot comparing persistent vector store accumulation across sequential queries Q01 through Q25.
Loads directly from benchmark/seed42/benchmark_results.csv.
Generates publication-quality SVG and 300-DPI PNG.
Strictly data-driven: all step progressions, plateau levels, admissions, and reinforcements
are dynamically computed from raw CSV rows without hardcoded query IDs, numbers, or memory UUIDs.
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate_fig6(
    csv_path: str = "benchmark/seed42/benchmark_results.csv",
    output_png: str = "manuscript/figures/png/fig6_memory_growth.png",
    output_svg: str = "manuscript/figures/svg/fig6_memory_growth.svg",
) -> None:
    os.makedirs(os.path.dirname(output_png) or '.', exist_ok=True)
    os.makedirs(os.path.dirname(output_svg) or '.', exist_ok=True)
    
    # Load raw benchmark CSV
    df = pd.read_csv(csv_path)
    m4 = df[df['mode'].str.startswith('Mode 4')].sort_values('query_id')
    m3 = df[df['mode'].str.startswith('Mode 3')].sort_values('query_id')
    
    queries = m4['query_id'].tolist()
    x = np.arange(len(queries))
    
    # Calculate exact cumulative store sizes dynamically from row sequence
    m4_store = []
    cnt4 = 0
    admissions = []
    reinforcements = []

    for idx, (_, r) in enumerate(m4.iterrows()):
        adm = r.get('memory_admission')
        reinf = r.get('memory_reinforcement')
        if adm == 'ADMITTED':
            cnt4 += 1
            admissions.append({
                "idx": idx,
                "query_id": r['query_id'],
                "store_size": cnt4,
            })
        elif adm == 'EXISTING_REINFORCED' or (pd.notna(reinf) and str(reinf).strip() and str(reinf).strip() != 'nan'):
            reinforcements.append({
                "idx": idx,
                "query_id": r['query_id'],
                "store_size": cnt4,
                "mem_id": str(reinf).strip() if pd.notna(reinf) else "Reinforced",
            })
        m4_store.append(cnt4)
        
    m3_store = []
    cnt3 = 0
    for _, r in m3.iterrows():
        if r['memory_admission'] == 'NAIVE_STORED':
            cnt3 += 1
        m3_store.append(cnt3)

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    plt.rcParams['font.sans-serif'] = 'Arial'
    
    final_m3 = m3_store[-1] if m3_store else 0
    final_m4 = m4_store[-1] if m4_store else 0

    # Plot Step curves
    ax.step(x, m3_store, where='post', label=f'Mode 3: Naive Vector RAG (Unconstrained Growth -> {final_m3} memories)',
            color='#c0392b', linewidth=2.2, linestyle='--', marker='s', markersize=4.5)
    ax.step(x, m4_store, where='post', label=f'Mode 4: Full ARMG (Governed Store -> Invariant at {final_m4} memories)',
            color='#1b4f72', linewidth=2.5, marker='o', markersize=5.5)
    
    # Highlight invariant plateau for Mode 4 dynamically
    plateau_start = len(queries) - 1
    if final_m4 in m4_store:
        plateau_start = m4_store.index(final_m4)

    if plateau_start < len(queries):
        start_q = queries[plateau_start]
        end_q = queries[-1]
        ax.axvspan(plateau_start, len(queries) - 1, color='#d4edda', alpha=0.35,
                   label=f'Mode 4 Invariant Plateau ({start_q}-{end_q}: Store = {final_m4})')
    
    # Dynamically annotate admissions
    for i, adm in enumerate(admissions):
        is_plateau = (adm["store_size"] == final_m4)
        label_text = f"{adm['query_id']}: Admitted\nStore = {adm['store_size']}"
        if is_plateau:
            label_text += " (Final Plateau)"
        
        # Stagger annotation positions cleanly
        y_text = 4 + (i * 3) if not is_plateau else 12
        x_text = max(0, adm["idx"] - 2)
        
        ax.annotate(label_text, xy=(adm["idx"], adm["store_size"]), xytext=(x_text, y_text),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color='#1b4f72'),
                    fontsize=8, fontweight='bold', color='#1b4f72',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#aed6f1'))
    
    # Dynamically annotate reinforcements
    for reinf in reinforcements:
        reinf_text = (
            f"{reinf['query_id']}: Mutual Exclusion Invariant\n"
            f"{reinf['mem_id']} Reinforced;\n"
            f"Admission Suppressed (Store = {reinf['store_size']})"
        )
        x_text = min(len(queries) - 6, reinf["idx"] - 1)
        ax.annotate(reinf_text, xy=(reinf["idx"], reinf["store_size"]), xytext=(x_text, 7),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color='#1e8449'),
                    fontsize=8, fontweight='bold', color='#1e8449',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#abebc6'))

    # Dynamically annotate Mode 3 final point
    if queries:
        ax.annotate(f"Mode 3 Final Size:\n{final_m3} Unmanaged Entries",
                    xy=(len(queries) - 1, final_m3),
                    xytext=(max(0, len(queries) - 6), min(21, final_m3)),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color='#c0392b'),
                    fontsize=8, fontweight='bold', color='#c0392b',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#f5b7b1'))

    ax.set_title('Persistent Memory Store Growth: Full ARMG vs. Naive Vector RAG',
                 fontsize=10.5, fontweight='bold', pad=12)
    ax.set_xlabel('Benchmark Query Sequence Execution Order', fontsize=9.5, fontweight='bold')
    ax.set_ylabel('Persistent Memory Store Size (Records)', fontsize=9.5, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(queries, fontsize=8, rotation=45)
    ax.set_xlim(-0.5, len(queries) - 0.5)
    ax.set_ylim(-0.5, max(final_m3 + 2.5, 25.5))
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.95)

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.close()
    print("Fig 6 generated successfully: PNG and SVG.")

if __name__ == '__main__':
    generate_fig6()
