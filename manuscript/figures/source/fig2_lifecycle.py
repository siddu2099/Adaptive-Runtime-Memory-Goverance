"""
Figure 2: ARMG Runtime Memory Lifecycle State Transition Machine
Illustrates the 6 discrete operational states and exact mathematical transitions from memory/governance.py.
Corrected with:
- Spacious 3-tier, 4-column layout eliminating text overlaps and box collisions.
- Clear, unambiguous arrow routing with dedicated whitespace corridors for all mathematical labels.
- Parallel vertical transition channels for ACTIVE <-> DECAYING reactivation and decay.
- Dedicated card for continuous temporal decay control law and benchmark execution status.
- Strict preservation of all numerical thresholds: Utility_0 >= 0.25, alpha=0.10, beta=0.15, lambda=0.05/day, C < 0.20, C < 0.15, 30 days.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_fig2():
    os.makedirs('manuscript/figures/png', exist_ok=True)
    os.makedirs('manuscript/figures/svg', exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(15.5, 9.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # State box colors (Curated publication palette with semantic meaning)
    c_new_bg = '#e6f7ff'
    c_new_border = '#1890ff'
    c_active_bg = '#e6fffb'
    c_active_border = '#13c2c2'
    c_stable_bg = '#f6ffed'
    c_stable_border = '#52c41a'
    c_decay_bg = '#fffbe6'
    c_decay_border = '#faad14'
    c_archive_bg = '#f5f5f5'
    c_archive_border = '#595959'
    c_delete_bg = '#fff1f0'
    c_delete_border = '#f5222d'
    
    c_edge = '#262626'
    c_success = '#2b8a3e'
    c_penalty = '#cf1322'
    c_decay = '#d48806'
    
    # Helper to draw a state box with spacious padding
    def draw_state(x, y, w, h, name, desc, bg, border, title_color='#111111'):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.5",
                                     facecolor=bg, edgecolor=border, linewidth=2.0)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 2.8, name, ha='center', va='center',
                fontsize=11.0, fontweight='bold', color=title_color)
        ax.text(x + w/2, y + (h - 2.8)/2, desc, ha='center', va='center',
                fontsize=8.0, color='#333333', linespacing=1.3)

    # =========================================================================
    # CANDIDATE KNOWLEDGE ENTRY & ADMISSION GATING (Column 0: x: 1.5 to 11.5)
    # =========================================================================
    # Candidate Box: centered vertically with the top tier (y: 69 to 81)
    cand_box = patches.FancyBboxPatch((1.5, 69.5), 10.5, 11.5, boxstyle="round,pad=0.5,rounding_size=1.0",
                                      facecolor='#ffffff', edgecolor='#8c8c8c', linewidth=1.5)
    ax.add_patch(cand_box)
    ax.text(6.75, 75.25, "Candidate\nRuntimeKnowledge\n(Post-Repair)", ha='center', va='center',
            fontsize=8.0, fontweight='bold', color='#111111', linespacing=1.2)

    # Admission arrow: Candidate (x=12.0) -> NEW (x=21.0) at y=75.25
    ax.annotate("", xy=(21.0, 75.25), xytext=(12.0, 75.25),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_edge))
    ax.text(16.5, 78.0, "Utility_0 >= 0.25\n(Admission Gate)", ha='center', va='bottom',
            fontsize=7.4, color='#096dd9', fontweight='bold', linespacing=1.1)

    # Rejection arrow (Downward from Candidate)
    ax.annotate("", xy=(6.75, 60.5), xytext=(6.75, 69.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_penalty, ls='--'))
    ax.text(6.75, 57.5, "Utility_0 < 0.25 OR\nTerminal Failure\n(Rejected)", ha='center', va='top',
            fontsize=7.2, color=c_penalty, style='italic', linespacing=1.1)

    # =========================================================================
    # TOP TIER: NOMINAL LIFECYCLE (y: 67.5 to 83.5)
    # States: NEW (Col 1), ACTIVE (Col 2), STABLE (Col 3)
    # =========================================================================

    # STATE 1: NEW (x: 21.0 to 36.0, y: 67.5 to 83.5)
    draw_state(21.0, 67.5, 15.0, 16.0, "NEW",
               "C_0 = 0.50\nFreshly Admitted\nZero Reinforcements",
               c_new_bg, c_new_border, title_color='#096dd9')

    # NEW -> ACTIVE (Upon first successful application)
    # Forward arrow pointing FROM NEW (x=36.0) TO ACTIVE (x=52.0) at y=75.5 (Gap: 16 units)
    ax.annotate("", xy=(52.0, 75.5), xytext=(36.0, 75.5),
                arrowprops=dict(arrowstyle="->", lw=2.0, color=c_success))
    ax.text(44.0, 78.0, "First Success:\nC_{t+1} = C_0 + alpha*(1-C_0)\n(alpha = 0.10 -> C=0.55)",
            ha='center', va='bottom', fontsize=7.4, color=c_success, fontweight='bold', linespacing=1.2)

    # STATE 2: ACTIVE (x: 52.0 to 67.0, y: 67.5 to 83.5)
    draw_state(52.0, 67.5, 15.0, 16.0, "ACTIVE",
               "0.50 <= C < 0.80\nActively Retrieved\n(Operational Memory)",
               c_active_bg, c_active_border, title_color='#006d75')

    # ACTIVE -> STABLE (Upon confidence reaching >= 0.80)
    # Forward arrow pointing FROM ACTIVE (x=67.0) TO STABLE (x=83.0) at y=75.5 (Gap: 16 units)
    ax.annotate("", xy=(83.0, 75.5), xytext=(67.0, 75.5),
                arrowprops=dict(arrowstyle="->", lw=2.0, color=c_success))
    ax.text(75.0, 78.0, "Successive Reinforcement:\nC >= 0.80 (Stable Gate)\n(Protected Baseline)",
            ha='center', va='bottom', fontsize=7.4, color=c_success, fontweight='bold', linespacing=1.2)

    # STATE 3: STABLE (x: 83.0 to 97.5, y: 67.5 to 83.5)
    draw_state(83.0, 67.5, 14.5, 16.0, "STABLE",
               "C >= 0.80\nHigh-Confidence Pattern\nProtected Baseline",
               c_stable_bg, c_stable_border, title_color='#237804')

    # Self-loop on STABLE (Repeated reinforcement with ample headroom)
    ax.plot([86.5, 86.5], [83.5, 91.0], color=c_success, lw=1.6)
    ax.plot([86.5, 94.0], [91.0, 91.0], color=c_success, lw=1.6)
    ax.annotate("", xy=(94.0, 83.5), xytext=(94.0, 91.0),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_success))
    ax.text(90.25, 93.0, "Success Reinforce: C_{t+1} = C_t + alpha*(1-C_t)",
            ha='center', va='bottom', fontsize=7.3, color=c_success, fontweight='bold')

    # =========================================================================
    # MIDDLE TIER: GOVERNANCE & DEGRADATION (y: 36.5 to 52.5)
    # States: ARCHIVED (Col 1), DECAYING (Col 2), Decay Note Card (Col 3)
    # =========================================================================

    # Failure penalty: ACTIVE -> ARCHIVED (if C drops < 0.20 via beta penalty)
    # Clean diagonal route from ACTIVE bottom-left (52.0, 69.5) to ARCHIVED top-right (36.0, 51.0)
    ax.annotate("", xy=(36.0, 51.0), xytext=(52.0, 69.5),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_penalty, ls='--'))
    ax.text(42.5, 63.5, "Failure Penalty: C * (1-beta)\n(beta = 0.15; if C < 0.20)",
            ha='center', va='center', fontsize=7.2, color=c_penalty, fontweight='bold', linespacing=1.1,
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#ffa39e', lw=0.8))

    # STATE 4: ARCHIVED (x: 21.0 to 36.0, y: 36.5 to 52.5)
    draw_state(21.0, 36.5, 15.0, 16.0, "ARCHIVED",
               "0.15 <= C < 0.20\nExcluded from Retrieval\nCandidate for Pruning",
               c_archive_bg, c_archive_border, title_color='#262626')

    # Demotion from DECAYING -> ARCHIVED (Horizontal arrow pointing left to ARCHIVED)
    ax.annotate("", xy=(36.0, 44.5), xytext=(52.0, 44.5),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_edge))
    ax.text(44.0, 47.0, "Decay: C < 0.20\n(Archival Gate)", ha='center', va='bottom',
            fontsize=7.5, color='#262626', fontweight='bold', linespacing=1.1)

    # STATE 5: DECAYING (x: 52.0 to 67.0, y: 36.5 to 52.5)
    draw_state(52.0, 36.5, 15.0, 16.0, "DECAYING",
               "Aging without reuse\nC(t) decays exponentially\n0.20 <= C < 0.80",
               c_decay_bg, c_decay_border, title_color='#ad6800')

    # -------------------------------------------------------------------------
    # Parallel vertical lanes between ACTIVE (Col 2 top) and DECAYING (Col 2 mid):
    # Lane A (Left, x=55.5): Reactivation (DECAYING -> ACTIVE) in green pointing UP
    # Lane B (Right, x=63.5): Inactivity decay (ACTIVE -> DECAYING) in amber dashed pointing DOWN
    # -------------------------------------------------------------------------
    
    # Reactivation: DECAYING -> ACTIVE
    ax.annotate("", xy=(55.5, 67.5), xytext=(55.5, 52.5),
                arrowprops=dict(arrowstyle="->", lw=2.0, color=c_success))
    ax.text(54.5, 60.0, "Re-applied &\nReinforced", ha='right', va='center',
            fontsize=7.4, color=c_success, fontweight='bold', linespacing=1.2)

    # Inactivity Decay: ACTIVE -> DECAYING
    ax.annotate("", xy=(63.5, 52.5), xytext=(63.5, 67.5),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_decay, ls='-.'))
    ax.text(64.5, 60.0, "Inactivity\nDecay", ha='left', va='center',
            fontsize=7.4, color=c_decay, fontweight='bold', linespacing=1.2)

    # STABLE -> DECAYING (Temporal Decay from STABLE)
    # Routes from STABLE bottom (85.0, 67.5) down-left to DECAYING right edge (67.0, 48.0)
    ax.annotate("", xy=(67.0, 48.0), xytext=(85.0, 67.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_decay, ls='-.'))
    ax.text(78.5, 61.5, "Decay from\nProtected State", ha='center', va='center',
            fontsize=7.0, color=c_decay, style='italic', linespacing=1.1,
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#ffe58f', lw=0.6))

    # Continuous Temporal Decay Callout Card (Column 3, middle tier: x: 73.0 to 97.5)
    decay_box = patches.FancyBboxPatch((73.0, 36.5), 24.5, 16.0, boxstyle="round,pad=0.5,rounding_size=1.0",
                                       facecolor='#fffbe6', edgecolor='#faad14', linewidth=1.4)
    ax.add_patch(decay_box)
    ax.text(85.25, 49.5, "Continuous Temporal Decay Law", ha='center', va='center',
            fontsize=8.2, fontweight='bold', color='#ad6800')
    ax.text(85.25, 45.8, "C(t) = C_ref * exp(-lambda * Delta t)", ha='center', va='center',
            fontsize=8.0, fontweight='bold', color='#111111')
    ax.text(85.25, 42.2, "Decay rate: lambda = 0.05 / day", ha='center', va='center',
            fontsize=7.4, color='#555555')
    ax.text(85.25, 39.0, "*Implemented & tested control law;\nunexercised in 3.5-min benchmark clock.",
            ha='center', va='center', fontsize=6.8, style='italic', color='#8c6b00', linespacing=1.1)

    # =========================================================================
    # BOTTOM TIER: TERMINAL PURGE (y: 6.0 to 22.0)
    # State: DELETED (Col 1, directly under ARCHIVED)
    # =========================================================================

    # STATE 6: DELETED (x: 22.0 to 38.0, y: 6.0 to 22.0)
    draw_state(22.0, 6.0, 16.0, 16.0, "DELETED",
               "Terminal Purge State\nPermanently Removed\nfrom FAISS Index",
               c_delete_bg, c_delete_border, title_color='#cf1322')

    # ARCHIVED -> DELETED (Downward arrow strictly pointing FROM ARCHIVED TO DELETED)
    ax.annotate("", xy=(30.0, 22.0), xytext=(30.0, 36.5),
                arrowprops=dict(arrowstyle="->", lw=2.2, color='#cf1322'))
    ax.text(31.8, 29.25, "Pruning Gate: C < 0.15 OR\nArchive Retention >= 30 days\n(Terminal Vector Deletion)",
            ha='left', va='center', fontsize=7.4, color='#cf1322', fontweight='bold', linespacing=1.2)

    plt.tight_layout()
    plt.savefig('manuscript/figures/png/fig2_lifecycle.png', dpi=300, bbox_inches='tight')
    plt.savefig('manuscript/figures/svg/fig2_lifecycle.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("Fig 2 generated successfully: PNG and SVG.")

if __name__ == '__main__':
    generate_fig2()

