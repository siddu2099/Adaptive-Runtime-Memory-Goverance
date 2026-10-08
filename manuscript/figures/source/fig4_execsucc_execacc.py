"""
Figure 4: PostgreSQL Execution Success vs. Relational Execution Accuracy Across All Six Experimental Modes.
Dynamically derives mean values and sample standard deviations from raw benchmark run CSVs
via benchmark.analysis.compute_benchmark_metrics().
Generates publication-quality SVG and 300-DPI PNG.
Per Audit 1 Remediation Item REM-P0-02.
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure repository root is on sys.path for direct script invocation
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from benchmark.analysis import compute_benchmark_metrics, MODE_LABELS

def generate_fig4(csv_paths=None, output_png='manuscript/figures/png/fig4_execsucc_execacc.png', output_svg='manuscript/figures/svg/fig4_execsucc_execacc.svg'):
    os.makedirs(os.path.dirname(output_png) or '.', exist_ok=True)
    os.makedirs(os.path.dirname(output_svg) or '.', exist_ok=True)
    
    # Programmatic metrics calculation directly from raw benchmark CSVs
    metrics_df = compute_benchmark_metrics(csv_paths=csv_paths)
    
    modes = [MODE_LABELS.get(m, m) for m in metrics_df["mode"]]
    exec_succ = metrics_df["exec_succ"].tolist()
    exec_acc  = metrics_df["exec_acc"].tolist()
    succ_err  = metrics_df["succ_std"].tolist()
    acc_err   = metrics_df["acc_std"].tolist()
    gaps      = [s - a for s, a in zip(exec_succ, exec_acc)]
    
    x = np.arange(len(modes))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    
    plt.rcParams['font.sans-serif'] = 'Arial'
    
    # Publication neutral color palette
    c_succ = '#2c3e50'  # Deep Navy Slate for Execution Success
    c_acc  = '#7f8c8d'  # Muted Gray for Relational Semantic Accuracy
    
    rects1 = ax.bar(x - width/2, exec_succ, width, yerr=succ_err, capsize=4,
                    label='PostgreSQL Execution Success (ExecSucc)', color=c_succ, edgecolor='#1a252f', linewidth=0.8)
    rects2 = ax.bar(x + width/2, exec_acc, width, yerr=acc_err, capsize=4,
                    label='Relational Execution Accuracy (ExecAcc)', color=c_acc, edgecolor='#566573', linewidth=0.8)
    
    # Value labels on top of bars
    for i in range(len(modes)):
        # ExecSucc label
        ax.text(x[i] - width/2, exec_succ[i] + 1.2, f"{exec_succ[i]:.1f}%",
                ha='center', va='bottom', fontsize=8, fontweight='bold', color=c_succ)
        # ExecAcc label
        ax.text(x[i] + width/2, exec_acc[i] + 1.2, f"{exec_acc[i]:.1f}%",
                ha='center', va='bottom', fontsize=8, color='#333333')
        # Annotate Discrepancy Gap
        ax.text(x[i], max(exec_succ[i], exec_acc[i]) + 6.5, f"Gap:\n{gaps[i]:.1f} pp",
                ha='center', va='bottom', fontsize=7.5, style='italic', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#e0e0e0', linewidth=0.5))

    ax.set_ylabel('Percentage (%)', fontsize=9.5, fontweight='bold')
    ax.set_title('PostgreSQL Execution Success vs. Relational Execution Accuracy Across Six Modes',
                 fontsize=10.5, fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(modes, fontsize=8.5)
    ax.set_ylim(0, 115)
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.95)
    
    # Draw horizontal plateau guide dynamically based on Mode 4 accuracy
    plateau_val = metrics_df.loc[metrics_df["mode"].str.startswith("Mode 4"), "exec_acc"].values[0]
    ax.axhline(plateau_val, color='#e74c3c', linestyle=':', linewidth=1.2, alpha=0.8)
    ax.text(5.4, plateau_val + 1.0, f'Semantic Accuracy Plateau ({plateau_val:.2f}%)', ha='right', va='bottom',
            fontsize=7.5, color='#c0392b', fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.close()
    print("Fig 4 generated successfully: PNG and SVG.")

if __name__ == '__main__':
    generate_fig4()
