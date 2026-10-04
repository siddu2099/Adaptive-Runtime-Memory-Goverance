"""
Figure 4: PostgreSQL Execution Success vs. Relational Execution Accuracy Across All Six Experimental Modes.
Loads exact mean values from Table II and evidence_package.md.
Generates publication-quality SVG and 300-DPI PNG.
"""
import os
import numpy as np
import matplotlib.pyplot as plt

def generate_fig4():
    os.makedirs('manuscript/figures/png', exist_ok=True)
    os.makedirs('manuscript/figures/svg', exist_ok=True)
    
    modes = [
        "Mode 1\n(Zero-Shot)",
        "Mode 2\n(Stateless Self-Corr)",
        "Mode 3\n(Naive RAG)",
        "Mode 4\n(Full ARMG)",
        "Mode 5\n(ARMG − NegConst)",
        "Mode 6\n(ARMG with λ=0)"
    ]
    
    # Frozen values from Table II (evidence_package.md Section D)
    exec_succ = [76.00, 92.00, 92.00, 96.00, 96.00, 94.67]
    exec_acc  = [57.33, 68.00, 68.00, 68.00, 68.00, 68.00]
    gaps      = [s - a for s, a in zip(exec_succ, exec_acc)]
    
    # Sample standard deviations over n=3 repeated runs
    succ_err = [0.00, 0.00, 0.00, 0.00, 0.00, 2.31]
    acc_err  = [2.31, 0.00, 0.00, 0.00, 0.00, 0.00]
    
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
    
    # Draw horizontal plateau guide at 68.00%
    ax.axhline(68.00, color='#e74c3c', linestyle=':', linewidth=1.2, alpha=0.8)
    ax.text(5.4, 69.0, 'Semantic Accuracy Plateau (68.00%)', ha='right', va='bottom',
            fontsize=7.5, color='#c0392b', fontweight='bold')

    plt.tight_layout()
    plt.savefig('manuscript/figures/png/fig4_execsucc_execacc.png', dpi=300, bbox_inches='tight')
    plt.savefig('manuscript/figures/svg/fig4_execsucc_execacc.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("Fig 4 generated successfully: PNG and SVG.")

if __name__ == '__main__':
    generate_fig4()
