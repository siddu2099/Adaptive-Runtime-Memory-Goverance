"""
Figure 5: Mode 2 vs. Full ARMG Operational Trade-Off Profile
Dynamically derives exact performance deltas across the five principal evaluation dimensions
directly from raw benchmark run CSVs via benchmark.analysis.
Generates publication-quality SVG and 300-DPI PNG.
Per Audit 1 Remediation Item REM-P0-02.
"""
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Ensure repository root is on sys.path for direct script invocation
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmark.analysis import compute_benchmark_metrics, compute_tradeoff_profile

def generate_fig5(csv_paths=None, output_png='manuscript/figures/png/fig5_tradeoff.png', output_svg='manuscript/figures/svg/fig5_tradeoff.svg'):
    os.makedirs(os.path.dirname(output_png) or '.', exist_ok=True)
    os.makedirs(os.path.dirname(output_svg) or '.', exist_ok=True)
    
    metrics = [
        "Mean Repair Iterations\n[Relative % Change]",
        "Mean Token Expenditure\n[Relative % Change]",
        "PostgreSQL Execution Success\n[Percentage Points]",
        "End-to-End Latency Overhead\n[Relative % Change]",
        "Relational Execution Accuracy\n[Percentage Points]"
    ]
    
    # Programmatic tradeoff metrics calculation directly from raw benchmark CSVs
    metrics_df = compute_benchmark_metrics(csv_paths=csv_paths)
    tradeoff = compute_tradeoff_profile(metrics_df)
    
    deltas = tradeoff["deltas"]
    units  = tradeoff["units"]
    labels = tradeoff["labels"]
    
    # Dynamic color coding based on metric semantics:
    # Overheads (retries, tokens, latency > 0) in orange; parity in gray; improvements in green/blue
    colors = []
    for i, val in enumerate(deltas):
        if i in (0, 1, 3):  # retries, tokens, latency
            colors.append('#d35400' if val > 0 else ('#27ae60' if val < 0 else '#7f8c8d'))
        else:  # success, accuracy
            colors.append('#2980b9' if val > 0 else ('#c0392b' if val < 0 else '#7f8c8d'))
    
    fig, ax = plt.subplots(figsize=(10.5, 5.5), dpi=300)
    plt.rcParams['font.sans-serif'] = 'Arial'
    
    y = np.arange(len(metrics))
    height = 0.55
    
    bars = ax.barh(y, deltas, height, color=colors, edgecolor='#2c3e50', linewidth=0.8)
    
    # Baseline line at 0
    ax.axvline(0, color='#2c3e50', linewidth=1.2)
    
    # Add text labels on the bars
    for i, bar in enumerate(bars):
        val = deltas[i]
        lbl = labels[i]
        if val < 0:
            ax.text(val - 1.2, bar.get_y() + bar.get_height()/2, lbl,
                    ha='right', va='center', fontsize=8.5, fontweight='bold', color='#1e8449')
        elif val > 0:
            ax.text(val + 1.2, bar.get_y() + bar.get_height()/2, lbl,
                    ha='left', va='center', fontsize=8.5, fontweight='bold', color='#d35400')
        else:
            ax.text(1.2, bar.get_y() + bar.get_height()/2, lbl,
                    ha='left', va='center', fontsize=8.5, fontweight='bold', color='#555555')

    ax.set_yticks(y)
    ax.set_yticklabels(metrics, fontsize=9, fontweight='bold')
    ax.invert_yaxis()  # Top-down order
    ax.set_xlim(-15, 62)
    ax.set_xlabel('Observed Delta (Mode 4 vs. Mode 2 Baseline)', fontsize=9.5, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.6)
    
    ax.set_title('Mode 4 (Full ARMG) vs. Mode 2 (Stateless Self-Correction) Operational Trade-Offs',
                 fontsize=10.5, fontweight='bold', pad=12)

    # Explanation legend box
    lbl0_short = labels[0].replace('\n', ' ')
    lbl1_short = labels[1].replace('\n', ' ')
    lbl2_short = labels[2].replace('\n', ' ')
    lbl3_short = labels[3].replace('\n', ' ')
    lbl4_short = labels[4].replace('\n', ' ')
    legend_text = (
        "Operational Trade-Off Summary:\n"
        f"• Orchestration Overhead: Retries ({lbl0_short}), Tokens ({lbl1_short}), Latency ({lbl3_short})\n"
        f"• Execution Recovery: PostgreSQL Success Parity ({lbl2_short})\n"
        f"• Semantic Reasoning: Relational Accuracy Parity ({lbl4_short})"
    )
    ax.text(-13, 4.3, legend_text, fontsize=8, color='#333333',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor='#ced4da'))

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.close()
    print("Fig 5 generated successfully: PNG and SVG.")

if __name__ == '__main__':
    generate_fig5()
