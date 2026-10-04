"""
Figure 6: Persistent Memory Store Growth: Full ARMG vs. Naive Vector RAG
Step plot comparing persistent vector store accumulation across sequential queries Q01 through Q25.
Loads directly from benchmark/seed42/benchmark_results.csv.
Generates publication-quality SVG and 300-DPI PNG.
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_fig6():
    os.makedirs('manuscript/figures/png', exist_ok=True)
    os.makedirs('manuscript/figures/svg', exist_ok=True)
    
    # Load raw benchmark CSV
    df = pd.read_csv('benchmark/seed42/benchmark_results.csv')
    m4 = df[df['mode'] == 'Mode 4 (Full ARMG)'].sort_values('query_id')
    m3 = df[df['mode'] == 'Mode 3 (Naive Vector RAG)'].sort_values('query_id')
    
    queries = m4['query_id'].tolist()
    x = np.arange(len(queries))
    
    # Calculate exact cumulative store sizes
    m4_store = []
    cnt4 = 0
    for _, r in m4.iterrows():
        if r['memory_admission'] == 'ADMITTED':
            cnt4 += 1
        m4_store.append(cnt4)
        
    m3_store = []
    cnt3 = 0
    for _, r in m3.iterrows():
        if r['memory_admission'] == 'NAIVE_STORED':
            cnt3 += 1
        m3_store.append(cnt3)

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    plt.rcParams['font.sans-serif'] = 'Arial'
    
    # Plot Step curves
    ax.step(x, m3_store, where='post', label='Mode 3: Naive Vector RAG (Unconstrained Growth -> 23 memories)',
            color='#c0392b', linewidth=2.2, linestyle='--', marker='s', markersize=4.5)
    ax.step(x, m4_store, where='post', label='Mode 4: Full ARMG (Governed Store -> Invariant at 3 memories)',
            color='#1b4f72', linewidth=2.5, marker='o', markersize=5.5)
    
    # Highlight invariant plateau for Mode 4
    ax.axvspan(14, 24, color='#d4edda', alpha=0.35, label='Mode 4 Invariant Plateau (Q15-Q25: Store = 3)')
    
    # Highlight specific admission and reinforcement events
    ax.annotate("Q04: Admitted (dim_geography)\nStore = 1", xy=(3, 1), xytext=(1, 5),
                arrowprops=dict(arrowstyle="->", lw=1.2, color='#1b4f72'),
                fontsize=8, fontweight='bold', color='#1b4f72',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#aed6f1'))
    
    ax.annotate("Q13: Admitted (Multi-join)\nStore = 2", xy=(12, 2), xytext=(8, 8),
                arrowprops=dict(arrowstyle="->", lw=1.2, color='#1b4f72'),
                fontsize=8, fontweight='bold', color='#1b4f72',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#aed6f1'))

    ax.annotate("Q15: Admitted (Window aggregation)\nStore = 3 (Final Plateau)", xy=(14, 3), xytext=(10, 12),
                arrowprops=dict(arrowstyle="->", lw=1.2, color='#1b4f72'),
                fontsize=8, fontweight='bold', color='#1b4f72',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#aed6f1'))

    ax.annotate("Q17: Mutual Exclusion Invariant\nmem-18fc8e84 Reinforced;\nAdmission Suppressed (Store = 3)",
                xy=(16, 3), xytext=(15, 7),
                arrowprops=dict(arrowstyle="->", lw=1.2, color='#1e8449'),
                fontsize=8, fontweight='bold', color='#1e8449',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#abebc6'))

    ax.annotate("Mode 3 Final Size:\n23 Unmanaged Entries", xy=(24, 23), xytext=(19, 21),
                arrowprops=dict(arrowstyle="->", lw=1.2, color='#c0392b'),
                fontsize=8, fontweight='bold', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#f5b7b1'))

    ax.set_title('Persistent Memory Store Growth: Full ARMG vs. Naive Vector RAG',
                 fontsize=10.5, fontweight='bold', pad=12)
    ax.set_xlabel('Benchmark Query Sequence Execution Order', fontsize=9.5, fontweight='bold')
    ax.set_ylabel('Persistent Memory Store Size (Records)', fontsize=9.5, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(queries, fontsize=8, rotation=45)
    ax.set_xlim(-0.5, 24.5)
    ax.set_ylim(-0.5, 25.5)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.95)

    plt.tight_layout()
    plt.savefig('manuscript/figures/png/fig6_memory_growth.png', dpi=300, bbox_inches='tight')
    plt.savefig('manuscript/figures/svg/fig6_memory_growth.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("Fig 6 generated successfully: PNG and SVG.")

if __name__ == '__main__':
    generate_fig6()
