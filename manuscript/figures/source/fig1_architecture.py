"""
Refined production script for Figure 1: End-to-End ARMG Architecture and Closed-Loop State Machine.
Generates publication-quality 300 DPI PNG and SVG with generous spacing, zero-overlap routing,
white-halo bridge crossings, and crisp IEEE typography.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_fig1_perfect():
    os.makedirs('manuscript/figures/png', exist_ok=True)
    os.makedirs('manuscript/figures/svg', exist_ok=True)
    os.makedirs('scratch', exist_ok=True)
    
    # 18.2 x 11.4 inches at 300 DPI gives ultra-crisp 5460 x 3420 resolution
    fig, ax = plt.subplots(figsize=(18.2, 11.4), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color Palette: Clean IEEE publication style with semantic differentiation
    c_slate_bg = '#f8fafc'
    c_slate_border = '#334155'
    c_amber_bg = '#fffbeb'
    c_amber_border = '#d97706'
    c_blue_bg = '#eff6ff'
    c_blue_border = '#2563eb'
    c_indigo_bg = '#f5f3ff'
    c_indigo_border = '#4f46e5'
    c_gov_bg = '#f0fdf4'
    c_gov_border = '#16a34a'
    
    c_text_dark = '#0f172a'
    c_text_muted = '#475569'
    c_edge = '#334155'
    c_reject = '#dc2626'
    c_success = '#16a34a'
    c_loop = '#2563eb'

    # Helper: draw a styled node container
    def draw_node(x, y, w, h, title, lines, bg, border, title_color='#0f172a'):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.5,rounding_size=1.2",
            facecolor=bg, edgecolor=border, linewidth=1.8
        )
        ax.add_patch(box)
        # Title text
        ax.text(
            x + w/2, y + h - 2.8, title,
            ha='center', va='center',
            fontsize=8.8, fontweight='bold', color=title_color
        )
        # Subtle horizontal divider under title
        ax.plot([x + 1.2, x + w - 1.2], [y + h - 4.5, y + h - 4.5], color=border, lw=0.6, alpha=0.35)
        # Body text
        body_y = y + (h - 4.5)/2
        ax.text(
            x + w/2, body_y, '\n'.join(lines),
            ha='center', va='center',
            fontsize=7.4, color=c_text_muted, linespacing=1.30
        )

    # =========================================================================
    # ROW 1: GENERATION PIPELINE & PRE-EXECUTION FILTERS (y: 72.0 to 88.0, h=16.0)
    # =========================================================================
    
    # User Query Input Box (left margin)
    q_box = patches.FancyBboxPatch(
        (1.5, 76.0), 7.2, 8.0,
        boxstyle="round,pad=0.4,rounding_size=1.0",
        facecolor='#ffffff', edgecolor='#64748b', linewidth=1.5
    )
    ax.add_patch(q_box)
    ax.text(
        5.1, 80.0, "User Query\n(Natural Lang)",
        ha='center', va='center',
        fontsize=7.8, fontweight='bold', color=c_text_dark, linespacing=1.2
    )

    # User Query -> Node 1 arrow
    ax.annotate(
        "", xy=(11.5, 80.0), xytext=(8.7, 80.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_edge, mutation_scale=12)
    )

    # Node 1: Intent Gate
    draw_node(
        11.5, 72.0, 14.5, 16.0,
        "Node 1: Intent Gate",
        ["Deterministic Fast-Path NLP", "Regex & Keyword Rules", "Blocks Destructive DDL/DML"],
        c_amber_bg, c_amber_border, title_color='#b45309'
    )

    # Node 1 -> Node 2 arrow (ALLOW corridor)
    ax.annotate(
        "", xy=(31.0, 80.0), xytext=(26.0, 80.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_success, mutation_scale=12)
    )
    ax.text(
        28.5, 82.2, "ALLOW",
        fontsize=7.2, color=c_success, fontweight='bold', ha='center', va='bottom',
        bbox=dict(boxstyle="round,pad=0.2", fc="#ffffff", ec=c_success, lw=0.8)
    )

    # Node 2: Introspect & Prune
    draw_node(
        31.0, 72.0, 14.0, 16.0,
        "Node 2: Introspect & Prune",
        ["PostgreSQL Catalog Introspection", "Zero-Token Schema Pruning", "Extract User Constraints"],
        c_slate_bg, c_slate_border
    )

    # Node 2 -> Node 3 arrow
    ax.annotate(
        "", xy=(49.5, 80.0), xytext=(45.0, 80.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_edge, mutation_scale=12)
    )

    # Node 3: Memory Retrieval
    draw_node(
        49.5, 72.0, 14.0, 16.0,
        "Node 3: Memory Retrieval",
        ["Unit-L2 nomic-embed (768d)", "FAISS CPU IndexFlatL2", "Filter: tau >= 0.50 & Active"],
        c_slate_bg, c_slate_border
    )

    # Node 3 -> Node 4 arrow
    ax.annotate(
        "", xy=(68.0, 80.0), xytext=(63.5, 80.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_edge, mutation_scale=12)
    )

    # Node 4: SQL Generator
    draw_node(
        68.0, 72.0, 14.0, 16.0,
        "Node 4: SQL Generator",
        ["qwen2.5:7b-instruct (Local)", "Greedy Decoding (temp=0.0)", "/ Manual SQL Override"],
        c_slate_bg, c_slate_border
    )

    # Node 4 -> Node 5 arrow
    ax.annotate(
        "", xy=(86.5, 80.0), xytext=(82.0, 80.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_edge, mutation_scale=12)
    )

    # Node 5: AST & Constraint Guard
    draw_node(
        86.5, 72.0, 12.5, 16.0,
        "Node 5: AST & Constraint Guard",
        ["SQLGlot Read-Only Check", "Projection Compliance", "Reject Table Substitution"],
        c_amber_bg, c_amber_border, title_color='#b45309'
    )

    # =========================================================================
    # ROW 2: EXECUTION, OBSERVATION & DIAGNOSIS (y: 43.0 to 59.0, h=16.0)
    # Right to Left flow: Node 6 -> Node 7 -> Node 8 -> Node 9
    # =========================================================================
    
    # Node 5 -> Node 6 (Valid Query: SELECT only & constraints met)
    ax.annotate(
        "", xy=(92.75, 59.0), xytext=(92.75, 72.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.8, color=c_success, mutation_scale=12)
    )
    ax.text(
        94.0, 65.5, "Valid Query\n(SELECT only &\nConstraints Met)",
        fontsize=6.8, color=c_success, fontweight='bold', va='center', ha='left', linespacing=1.15
    )

    # Node 6: PG Executor
    draw_node(
        86.5, 43.0, 12.5, 16.0,
        "Node 6: PG Executor",
        ["Physical PostgreSQL 18.1", "Read-Only Transaction", "Capture Rows / Stderr"],
        c_blue_bg, c_blue_border, title_color='#1d4ed8'
    )

    # Node 5 -> Node 7 (Rejection corridor: Mutation Rejection / Constraint Violation)
    ax.plot([86.5, 84.5], [74.5, 74.5], color=c_reject, lw=1.6, ls='--')
    ax.plot([84.5, 84.5], [74.5, 66.0], color=c_reject, lw=1.6, ls='--')
    ax.plot([84.5, 75.0], [66.0, 66.0], color=c_reject, lw=1.6, ls='--')
    ax.annotate(
        "", xy=(75.0, 59.0), xytext=(75.0, 66.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_reject, ls='--', mutation_scale=12)
    )
    ax.text(
        79.5, 67.8, "Mutation Rejection / Constraint Violation\n(STATUS_BLOCKED / STATUS_FAILED)",
        fontsize=6.6, color=c_reject, fontweight='bold', ha='center', va='bottom',
        bbox=dict(boxstyle="round,pad=0.25", fc="#ffffff", ec=c_reject, lw=0.8, alpha=0.95),
        linespacing=1.15
    )

    # Node 6 -> Node 7 (Driver Trace)
    ax.annotate(
        "", xy=(82.0, 51.0), xytext=(86.5, 51.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_edge, mutation_scale=12)
    )
    ax.text(
        84.25, 53.0, "Driver\nTrace",
        fontsize=6.8, color='#475569', ha='center', va='bottom', linespacing=1.1
    )

    # Node 7: Observation
    draw_node(
        68.0, 43.0, 14.0, 16.0,
        "Node 7: Observation",
        ["Capture RuntimeObservation", "Normalize Stderr Exceptions", "Preserve Immutable Context"],
        c_indigo_bg, c_indigo_border, title_color='#3730a3'
    )

    # Node 7 -> Node 8 (Failure)
    ax.annotate(
        "", xy=(63.5, 51.0), xytext=(68.0, 51.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_reject, mutation_scale=12)
    )
    ax.text(
        65.75, 53.0, "Failure",
        fontsize=7.0, color=c_reject, fontweight='bold', ha='center', va='bottom',
        bbox=dict(boxstyle="round,pad=0.2", fc="#ffffff", ec=c_reject, lw=0.7)
    )

    # Node 8: Diagnosis
    draw_node(
        49.5, 43.0, 14.0, 16.0,
        "Node 8: Diagnosis",
        ["Deterministic 7-Tier Taxonomy", "Extract Broken Identifiers", "Resolve Schema Remappings"],
        c_indigo_bg, c_indigo_border, title_color='#3730a3'
    )

    # Node 8 -> Node 9
    ax.annotate(
        "", xy=(45.0, 51.0), xytext=(49.5, 51.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_edge, mutation_scale=12)
    )

    # Node 9: Knowledge & Budget
    draw_node(
        31.0, 43.0, 14.0, 16.0,
        "Node 9: Knowledge & Budget",
        ["Synthesize RuntimeKnowledge", "Evaluate Retry Budget", "(K_max = 3 retries)"],
        c_indigo_bg, c_indigo_border, title_color='#3730a3'
    )

    # =========================================================================
    # ROW 3: REPAIR PROMPT, GOVERNANCE & TERMINAL OUTPUT (y: 6.0 to 28.0)
    # =========================================================================
    
    # Node 10: Repair Prompt
    draw_node(
        11.5, 10.0, 14.5, 17.0,
        "Node 10: Repair Prompt",
        ["[STRICT REPAIR CONSTRAINTS]", "Negative Identifiers & Rules", "Synthesize Next Candidate"],
        c_indigo_bg, c_indigo_border, title_color='#3730a3'
    )

    # Node 9 -> Node 10 (Retries remaining K <= 3)
    ax.plot([33.5, 33.5], [43.0, 34.0], color=c_loop, lw=1.8)
    ax.plot([33.5, 18.75], [34.0, 34.0], color=c_loop, lw=1.8)
    ax.annotate(
        "", xy=(18.75, 27.0), xytext=(18.75, 34.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.8, color=c_loop, mutation_scale=12)
    )
    ax.text(
        26.0, 35.5, "Retries Remaining (K <= 3)",
        fontsize=7.0, color=c_loop, fontweight='bold', ha='center', va='bottom',
        bbox=dict(boxstyle="round,pad=0.25", fc="#ffffff", ec=c_loop, lw=0.8)
    )

    # -------------------------------------------------------------------------
    # Node 10 Loopback to Node 4 (Clean perimeter loop with halo bridge)
    # -------------------------------------------------------------------------
    # Route: exit Node 10 left (11.5, 18.5) -> left to 0.7 -> up to 94.5 -> right to 75.0 -> down to Node 4 top (75.0, 88.0)
    
    # Halo bridge layer (white background mask to guarantee zero visual blending with crossings)
    ax.plot([11.5, 0.7], [18.5, 18.5], color='#ffffff', lw=4.0)
    ax.plot([0.7, 0.7], [18.5, 94.5], color='#ffffff', lw=4.0)
    ax.plot([0.7, 75.0], [94.5, 94.5], color='#ffffff', lw=4.0)
    ax.plot([75.0, 75.0], [94.5, 88.0], color='#ffffff', lw=4.0)

    # Core loop line
    ax.plot([11.5, 0.7], [18.5, 18.5], color=c_loop, lw=1.8)
    ax.plot([0.7, 0.7], [18.5, 94.5], color=c_loop, lw=1.8)
    ax.plot([0.7, 75.0], [94.5, 94.5], color=c_loop, lw=1.8)
    ax.annotate(
        "", xy=(75.0, 88.0), xytext=(75.0, 94.5),
        arrowprops=dict(arrowstyle="-|>", lw=1.8, color=c_loop, mutation_scale=14)
    )
    ax.text(
        42.0, 96.0, "Repair Feedback Loop (Bounded Retries K <= 3)",
        fontsize=8.5, color=c_loop, fontweight='bold', ha='center', va='bottom',
        bbox=dict(boxstyle="round,pad=0.3", fc="#ffffff", ec=c_loop, lw=1.0)
    )

    # -------------------------------------------------------------------------
    # Short-Circuit Route: Node 1 -> Node 11 (Destructive Intent Intercepted)
    # -------------------------------------------------------------------------
    # Runs safely around perimeter: drops from Node 1 (13.0, 72.0) down to 69.5,
    # left to x=0.35, down to y=2.2, then right under all nodes to x=54.0, up into Node 11.
    ax.plot([13.0, 13.0], [72.0, 69.5], color=c_reject, lw=1.6, ls='--')
    ax.plot([13.0, 0.35], [69.5, 69.5], color=c_reject, lw=1.6, ls='--')
    ax.plot([0.35, 0.35], [69.5, 2.2], color=c_reject, lw=1.6, ls='--')
    ax.plot([0.35, 54.0], [2.2, 2.2], color=c_reject, lw=1.6, ls='--')
    ax.annotate(
        "", xy=(54.0, 6.0), xytext=(54.0, 2.2),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_reject, ls='--', mutation_scale=12)
    )
    # Masked Pill Badge along bottom corridor (centered on y=2.2 so dashed line is cleanly masked behind it)
    ax.text(
        34.0, 2.2, "BLOCK / AMBIGUOUS: Destructive Intent Intercepted  (0 Model Tokens | 0 DB Calls | STATUS_BLOCKED)",
        fontsize=6.8, color=c_reject, fontweight='bold', ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec=c_reject, lw=0.9)
    )

    # Node 9 -> Node 11 (Budget Exhausted K > 3)
    ax.plot([42.0, 42.0], [43.0, 31.5], color=c_reject, lw=1.6, ls=':')
    ax.plot([42.0, 44.0], [31.5, 31.5], color=c_reject, lw=1.6, ls=':')
    ax.annotate(
        "", xy=(44.0, 28.0), xytext=(44.0, 31.5),
        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=c_reject, ls=':', mutation_scale=12)
    )
    ax.text(
        43.0, 33.0, "Budget Exhausted (STATUS_FAILED)",
        fontsize=6.8, color=c_reject, fontweight='bold', ha='center', va='bottom',
        bbox=dict(boxstyle="round,pad=0.2", fc="#ffffff", ec=c_reject, lw=0.7)
    )

    # Node 7 -> Node 11 (Terminal Outcome: Success, Blocked, Failed)
    ax.annotate(
        "", xy=(75.0, 28.0), xytext=(75.0, 43.0),
        arrowprops=dict(arrowstyle="-|>", lw=1.8, color=c_success, mutation_scale=14)
    )
    ax.text(
        76.2, 35.5, "Terminal Outcome:\nSTATUS_SUCCESS,\nSTATUS_BLOCKED, or\nSTATUS_FAILED",
        fontsize=7.0, color='#15803d', fontweight='bold', va='center', ha='left', linespacing=1.2,
        bbox=dict(boxstyle="round,pad=0.25", fc="#ffffff", ec=c_success, lw=0.8)
    )

    # -------------------------------------------------------------------------
    # Node 11: memory_governance_node (Closed-Loop Governance Container)
    # Spans x: 31.0 to 86.0 (w=55.0), y: 6.0 to 28.0 (h=22.0)
    # -------------------------------------------------------------------------
    box11 = patches.FancyBboxPatch(
        (31.0, 6.0), 55.0, 22.0,
        boxstyle="round,pad=0.6,rounding_size=1.5",
        facecolor=c_gov_bg, edgecolor=c_gov_border, linewidth=2.2
    )
    ax.add_patch(box11)
    ax.text(
        58.5, 25.8, "Node 11: memory_governance_node",
        ha='center', va='center',
        fontsize=10.2, fontweight='bold', color='#14532d'
    )
    ax.text(
        58.5, 23.8, "Closed-Loop Governance Engine (Terminal State Processing)",
        ha='center', va='center',
        fontsize=8.0, style='italic', color='#334155'
    )

    # Internal sub-panel: REINFORCEMENT BRANCH
    p_left = patches.FancyBboxPatch(
        (32.8, 8.0), 25.0, 13.8,
        boxstyle="round,pad=0.4,rounding_size=1.0",
        facecolor='#ffffff', edgecolor='#86efac', lw=1.4
    )
    ax.add_patch(p_left)
    ax.text(45.3, 19.8, "REINFORCEMENT BRANCH", fontsize=8.0, fontweight='bold', color='#15803d', ha='center')
    ax.plot([34.0, 56.6], [18.5, 18.5], color='#86efac', lw=0.8)
    ax.text(45.3, 16.8, "Trigger: Applied Memory Present (M_applied)", fontsize=7.2, color='#334155', ha='center')
    ax.text(45.3, 14.2, "Escalate: C_{t+1} = C_t + alpha*(1 - C_t)", fontsize=7.2, color='#1d4ed8', fontweight='bold', ha='center')
    ax.text(45.3, 11.6, "Suppress New Admission (Mutual Exclusion Invariant)", fontsize=6.8, color='#475569', style='italic', ha='center')
    ax.text(45.3, 9.4, "Action = Reinforce(M_applied)", fontsize=7.0, color='#15803d', fontweight='bold', ha='center')

    # Internal sub-panel: ADMISSION & INTEGRITY BRANCH
    p_right = patches.FancyBboxPatch(
        (59.2, 8.0), 25.0, 13.8,
        boxstyle="round,pad=0.4,rounding_size=1.0",
        facecolor='#ffffff', edgecolor='#86efac', lw=1.4
    )
    ax.add_patch(p_right)
    ax.text(71.7, 19.8, "ADMISSION & INTEGRITY BRANCH", fontsize=8.0, fontweight='bold', color='#15803d', ha='center')
    ax.plot([60.4, 83.0], [18.5, 18.5], color='#86efac', lw=0.8)
    ax.text(71.7, 16.8, "Trigger: Success without Prior Memory & Retries > 0", fontsize=7.2, color='#334155', ha='center')
    ax.text(71.7, 14.2, "Admission Gate: Utility_0 >= 0.25 -> NEW State", fontsize=7.2, color='#15803d', fontweight='bold', ha='center')
    ax.text(71.7, 11.6, "Blocked / Constraint Failed -> Zero Admission (Action = \u2205)", fontsize=6.8, color='#b91c1c', style='italic', ha='center')
    ax.text(71.7, 9.4, "Quarantine: MemoryState.ARCHIVED Excludes from Retrieval", fontsize=7.0, color='#b45309', fontweight='bold', ha='center')

    # Terminal Exit Arrow to Final Output
    ax.annotate(
        "", xy=(89.5, 17.0), xytext=(86.0, 17.0),
        arrowprops=dict(arrowstyle="-|>", lw=2.0, color=c_edge, mutation_scale=14)
    )
    
    # Final Output Box: spans x: 89.5 to 98.8, y: 13.0 to 21.0
    out_box = patches.FancyBboxPatch(
        (89.5, 13.0), 9.3, 8.0,
        boxstyle="round,pad=0.4,rounding_size=1.0",
        facecolor='#ffffff', edgecolor='#475569', linewidth=1.5
    )
    ax.add_patch(out_box)
    ax.text(
        94.15, 17.0, "Final Output\n(Result / Status)",
        ha='center', va='center',
        fontsize=8.0, fontweight='bold', color=c_text_dark, linespacing=1.2
    )

    plt.tight_layout()
    # Save to all authoritative locations
    plt.savefig('manuscript/figures/png/fig1_architecture.png', dpi=300, bbox_inches='tight')
    plt.savefig('manuscript/figures/svg/fig1_architecture.svg', format='svg', bbox_inches='tight')
    plt.savefig('fig1_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Fig 1 generated successfully in manuscript/figures/ and workspace root.")

if __name__ == '__main__':
    generate_fig1_perfect()
