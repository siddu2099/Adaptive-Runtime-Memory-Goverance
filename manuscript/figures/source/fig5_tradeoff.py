"""
Figure 5: Mode 2 vs. Full ARMG Operational Trade-Off Profile
Illustrates the exact performance deltas across the five principal evaluation dimensions.
Explicitly distinguishes relative percentage changes (%) from percentage-point changes (pp).
Generates publication-quality SVG and 300-DPI PNG.
"""
import os
import matplotlib.pyplot as plt
import numpy as np

def generate_fig5():
    os.makedirs('manuscript/figures/png', exist_ok=True)
    os.makedirs('manuscript/figures/svg', exist_ok=True)
    
    metrics = [
        "Mean Repair Iterations\n[Relative % Change]",
        "Mean Token Expenditure\n[Relative % Change]",
        "PostgreSQL Execution Success\n[Percentage Points]",
        "End-to-End Latency Overhead\n[Relative % Change]",
        "Relational Execution Accuracy\n[Percentage Points]"
    ]
    
    # Deltas: Mode 4 vs Mode 2
    # Retries: -34.38% (0.28 vs 0.43)
    # Tokens: -5.30% (542.37 vs 572.72)
    # ExecSucc: +4.00 pp (96.00% vs 92.00%)
    # Latency: +19.79% (8,564.89 vs 7,149.68 ms)
    # ExecAcc: 0.00 pp (68.00% vs 68.00%)
    deltas = [-34.38, -5.30, 4.00, 19.79, 0.00]
    units  = ["%", "%", "pp", "%", "pp"]
    labels = [
        "-34.38%\n(0.28 vs 0.43 retries)",
        "-5.30%\n(542.4 vs 572.7 tok)",
        "+4.00 pp\n(96.0% vs 92.0%)",
        "+19.79%\n(8,564.9 vs 7,149.7 ms)",
        "0.00 pp\n(68.00% Parity)"
    ]
    
    # Color coding: Green for efficiency gains, Orange for operational cost (latency), Gray for neutral
    colors = ['#27ae60', '#27ae60', '#2980b9', '#d35400', '#7f8c8d']
    
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
            c = '#d35400' if i == 3 else '#1a5276'
            ax.text(val + 1.2, bar.get_y() + bar.get_height()/2, lbl,
                    ha='left', va='center', fontsize=8.5, fontweight='bold', color=c)
        else:
            ax.text(1.2, bar.get_y() + bar.get_height()/2, lbl,
                    ha='left', va='center', fontsize=8.5, fontweight='bold', color='#555555')

    ax.set_yticks(y)
    ax.set_yticklabels(metrics, fontsize=9, fontweight='bold')
    ax.invert_yaxis()  # Top-down order
    ax.set_xlim(-48, 38)
    ax.set_xlabel('Observed Delta (Mode 4 vs. Mode 2 Baseline)', fontsize=9.5, fontweight='bold')
    ax.grid(axis='x', linestyle=':', alpha=0.6)
    
    ax.set_title('Mode 4 (Full ARMG) vs. Mode 2 (Stateless Self-Correction) Operational Trade-Offs',
                 fontsize=10.5, fontweight='bold', pad=12)

    # Explanation legend box
    legend_text = (
        "Engineering Trade-Off Summary:\n"
        "• Relative Reductions: Mean Retries (-34.38%), Token Expenditure (-5.30%)\n"
        "• Percentage-Point Recovery: Physical PostgreSQL Execution Success (+4.00 pp)\n"
        "• Architectural Overhead: End-to-End Latency Penalty (+19.79%)\n"
        "• Semantic Accuracy: Exact Parity at 68.00% (0.00 pp change)"
    )
    ax.text(-46, 4.3, legend_text, fontsize=8, color='#333333',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor='#ced4da'))

    plt.tight_layout()
    plt.savefig('manuscript/figures/png/fig5_tradeoff.png', dpi=300, bbox_inches='tight')
    plt.savefig('manuscript/figures/svg/fig5_tradeoff.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("Fig 5 generated successfully: PNG and SVG.")

if __name__ == '__main__':
    generate_fig5()
