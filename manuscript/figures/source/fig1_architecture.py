"""
Figure 1: End-to-End ARMG Architecture and Closed-Loop State Machine
Canonical 11-node LangGraph execution state machine matching graph/workflow.py.
Features:
- Complete 11-node pipeline including Node 1 Intent Safety Gate and Node 5 Dual AST/Constraint Guard.
- Zero-token early exit corridor from Node 1 directly to Node 11 on destructive/ambiguous intent.
- Pre-execution AST guardrail and explicit user-constraint validation corridors.
- Clean perimeter loopback routing well outside User Query box (zero line crossings).
- Generous padding, margins, and crisp typography adhering to IEEE standards.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_fig1():
    os.makedirs('manuscript/figures/png', exist_ok=True)
    os.makedirs('manuscript/figures/svg', exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(16.5, 10.0), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Palette: Professional publication neutral with semantic accents
    c_node_bg = '#f8f9fa'
    c_node_border = '#2b2d42'
    c_guard_bg = '#fff9db'
    c_guard_border = '#d48806'
    c_exec_bg = '#e6f7ff'
    c_exec_border = '#096dd9'
    c_repair_bg = '#f0f5ff'
    c_repair_border = '#1d39c4'
    c_gov_bg = '#f4fbf0'
    c_gov_border = '#2b8a3e'
    c_edge = '#2b2d42'
    c_reject = '#cf1322'
    c_success = '#2b8a3e'
    c_loop = '#096dd9'
    
    # Helper to draw a standard node box with proper padding
    def draw_node(x, y, w, h, title, subtext, bg, border, title_color='#111111'):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
                                     facecolor=bg, edgecolor=border, linewidth=1.8)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 2.8, title, ha='center', va='center',
                fontsize=8.8, fontweight='bold', color=title_color)
        ax.text(x + w/2, y + (h - 2.8)/2, subtext, ha='center', va='center',
                fontsize=7.4, color='#333333', linespacing=1.22)

    # =========================================================================
    # ROW 1: GENERATION PIPELINE & PRE-EXECUTION FILTERS (y: 72 to 87)
    # Nodes: User Query, Node 1 (Intent Gate), Node 2 (Introspect), Node 3 (Retrieval), Node 4 (SQL Gen), Node 5 (AST/Constraint Guard)
    # =========================================================================
    
    # User Query Input Box: positioned at far left
    q_box = patches.FancyBboxPatch((1.5, 76.5), 7.5, 6.0, boxstyle="round,pad=0.4,rounding_size=1.0",
                                   facecolor='#ffffff', edgecolor='#666666', linewidth=1.4)
    ax.add_patch(q_box)
    ax.text(5.25, 79.5, "User Query\n(Natural Lang)", ha='center', va='center',
            fontsize=7.8, fontweight='bold', color='#111111', linespacing=1.2)

    # User Query -> Node 1 arrow
    ax.annotate("", xy=(11.0, 79.5), xytext=(9.0, 79.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 1: intent_gate_node
    draw_node(11.0, 72.0, 14.5, 15.0, "Node 1: Intent Gate",
              "Deterministic NLP Filter\nFast-Path Keyword/Regex\nBlocks Destructive DDL/DML",
              c_guard_bg, c_guard_border, title_color='#ad6800')

    # Node 1 -> Node 2 arrow (Safe / Analytical Query)
    ax.annotate("", xy=(28.5, 79.5), xytext=(25.5, 79.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_success))
    ax.text(27.0, 81.3, "ALLOW", fontsize=7.0, color=c_success, fontweight='bold', ha='center')

    # Node 1 -> Node 11 Short-Circuit Corridor (BLOCK / AMBIGUOUS)
    # Routes down from Node 1 left-bottom, drops through corridor at x=10.0 down to y=20.0, into Node 11
    ax.plot([14.5, 14.5], [72.0, 68.0], color=c_reject, lw=1.6, ls='--')
    ax.plot([14.5, 9.5], [68.0, 68.0], color=c_reject, lw=1.6, ls='--')
    ax.plot([9.5, 9.5], [68.0, 19.5], color=c_reject, lw=1.6, ls='--')
    ax.plot([9.5, 33.0], [19.5, 19.5], color=c_reject, lw=1.6, ls='--')
    ax.annotate("", xy=(33.0, 19.5), xytext=(31.0, 19.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_reject, ls='--'))
    ax.text(9.0, 48.0, "BLOCK / AMBIGUOUS: Destructive Intent\n(0 Tokens | 0 DB Calls | STATUS_BLOCKED)",
            fontsize=6.8, color=c_reject, fontweight='bold', va='center', ha='right', rotation=90)

    # Node 2: introspect_and_prune_node
    draw_node(28.5, 72.0, 14.5, 15.0, "Node 2: Introspect & Prune",
              "Catalog Introspection\nZero-Token Pruning\nExtract User Constraints", c_node_bg, c_node_border)

    # Node 2 -> Node 3 arrow
    ax.annotate("", xy=(46.0, 79.5), xytext=(43.0, 79.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 3: memory_retrieval_node
    draw_node(46.0, 72.0, 14.5, 15.0, "Node 3: Memory Retrieval",
              "Unit-L2 nomic-embed\nFAISS CPU (tau >= 0.50)\nConstraint-Filtered Search", c_node_bg, c_node_border)

    # Node 3 -> Node 4 arrow
    ax.annotate("", xy=(63.5, 79.5), xytext=(60.5, 79.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 4: sql_generator_node
    draw_node(63.5, 72.0, 14.5, 15.0, "Node 4: SQL Generator",
              "qwen2.5:7b-instruct\nGreedy Decoding (temp=0.0)\n/ Manual SQL Override", c_node_bg, c_node_border)

    # Node 4 -> Node 5 arrow
    ax.annotate("", xy=(81.0, 79.5), xytext=(78.0, 79.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 5: ast_guard_node
    draw_node(81.0, 72.0, 17.5, 15.0, "Node 5: AST & Constraint Guard",
              "SQLGlot AST Read-Only Check\nProjection Column Verification\nProhibited Table Rejection",
              c_guard_bg, c_guard_border, title_color='#ad6800')

    # =========================================================================
    # ROW 2: EXECUTION, OBSERVATION & DIAGNOSIS (y: 43 to 58)
    # Nodes: Node 9 (Knowledge), Node 8 (Diagnosis), Node 7 (Observation), Node 6 (PG Executor)
    # =========================================================================
    
    # Node 5 -> Node 6 (Valid Query: SELECT only & Constraints Satisfied)
    ax.annotate("", xy=(89.75, 58.0), xytext=(89.75, 72.0),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_success))
    ax.text(91.0, 65.0, "Valid Query\n(SELECT only &\nConstraints Met)", fontsize=7.2, color=c_success,
            fontweight='bold', va='center', ha='left', linespacing=1.2)

    # Node 6: postgres_executor_node (Row 2, far right)
    draw_node(81.0, 43.0, 17.5, 15.0, "Node 6: PG Executor",
              "Physical PostgreSQL 18.1\nRead-Only Transaction\nCapture Rows / Stderr",
              c_exec_bg, c_exec_border, title_color='#096dd9')

    # Node 5 -> Node 7 (Safety / Constraint Rejection -> Blocked / Failed Observation)
    # Routed cleanly through inter-row corridor (y=64.5), completely avoiding Node 4
    ax.plot([81.0, 79.25], [74.5, 74.5], color=c_reject, lw=1.6, ls='--')
    ax.plot([79.25, 79.25], [74.5, 65.0], color=c_reject, lw=1.6, ls='--')
    ax.plot([79.25, 70.75], [65.0, 65.0], color=c_reject, lw=1.6, ls='--')
    ax.annotate("", xy=(70.75, 58.0), xytext=(70.75, 65.0),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_reject, ls='--'))
    ax.text(75.0, 66.8, "Mutation Rejection / Constraint Violation\n(STATUS_BLOCKED / STATUS_FAILED)", fontsize=6.8,
            color=c_reject, fontweight='bold', ha='center', va='bottom', linespacing=1.1)

    # Node 6 -> Node 7 (Raw driver execution trace)
    ax.annotate("", xy=(78.0, 50.5), xytext=(81.0, 50.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))
    ax.text(79.5, 52.8, "Driver\nTrace", fontsize=6.8, color='#555555',
            ha='center', va='bottom', linespacing=1.1)

    # Node 7: observation_node (Row 2, col 3)
    draw_node(63.5, 43.0, 14.5, 15.0, "Node 7: Observation",
              "Capture RuntimeObservation\nNormalize Stderr\nPreserve Raw State",
              c_repair_bg, c_repair_border, title_color='#1d39c4')

    # Node 7 -> Node 8 (Execution Failure)
    ax.annotate("", xy=(60.5, 50.5), xytext=(63.5, 50.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_reject))
    ax.text(62.0, 52.5, "Failure", fontsize=7.2, color=c_reject,
            fontweight='bold', ha='center', va='bottom')

    # Node 8: diagnosis_node (Row 2, col 2)
    draw_node(46.0, 43.0, 14.5, 15.0, "Node 8: Diagnosis",
              "Canonical 7-Tier Engine\nExtract Broken Identifiers\nConstraint-Bounded Candidates",
              c_repair_bg, c_repair_border, title_color='#1d39c4')

    # Node 8 -> Node 9 arrow
    ax.annotate("", xy=(43.0, 50.5), xytext=(46.0, 50.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 9: knowledge_node (Row 2, col 1)
    draw_node(28.5, 43.0, 14.5, 15.0, "Node 9: Knowledge & Budget",
              "Form RuntimeKnowledge\nEvaluate Retry Budget\n(K_max = 3 retries)",
              c_repair_bg, c_repair_border, title_color='#1d39c4')

    # =========================================================================
    # ROW 3: REPAIR LOOP & TERMINAL GOVERNANCE (y: 8 to 27)
    # =========================================================================
    
    # Node 9 -> Node 10 (If K <= 3 retries remaining)
    # Routed from Node 9 bottom-left (x=32.0, y=43.0) to Node 10 top (x=18.25, y=27.0)
    ax.plot([32.0, 32.0], [43.0, 36.0], color=c_loop, lw=1.8)
    ax.plot([32.0, 18.25], [36.0, 36.0], color=c_loop, lw=1.8)
    ax.annotate("", xy=(18.25, 27.0), xytext=(18.25, 36.0),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_loop))
    ax.text(25.0, 37.5, "Retries K <= 3 (STATUS_RETRYING)", fontsize=7.2,
            color=c_loop, fontweight='bold', va='bottom', ha='center')

    # Node 10: repair_prompt_node (Row 3, col 1)
    draw_node(11.0, 12.0, 14.5, 15.0, "Node 10: Repair Prompt",
              "[STRICT REPAIR CONSTRAINTS]\nNegative Identifiers & Rules\nPreserve Stated Constraints",
              c_repair_bg, c_repair_border, title_color='#1d39c4')

    # -------------------------------------------------------------------------
    # Node 10 Loopback to Node 4 (Clean perimeter routing outside User Query)
    # Route: Node 10 left (x=11.0, y=19.5) -> left to x=0.5 -> up to y=94.5 -> right to x=70.75 -> down to Node 4 top (y=87.0)
    # User Query box is at x: 1.5 to 9.0, so x=0.5 has clean safety margin
    # -------------------------------------------------------------------------
    ax.plot([11.0, 0.5], [19.5, 19.5], color=c_loop, lw=1.8)
    ax.plot([0.5, 0.5], [19.5, 94.5], color=c_loop, lw=1.8)
    ax.plot([0.5, 70.75], [94.5, 94.5], color=c_loop, lw=1.8)
    ax.annotate("", xy=(70.75, 87.0), xytext=(70.75, 94.5),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_loop))
    ax.text(38.0, 96.0, "Repair Feedback Loop (Max K = 3 Retries)", fontsize=8.5,
            color=c_loop, fontweight='bold', ha='center', va='bottom')

    # Node 9 -> Node 11 (If Budget Exhausted K > 3)
    # Routes out of Node 9 bottom-right into Node 11 top-left
    ax.plot([38.0, 38.0], [43.0, 31.0], color=c_reject, lw=1.6, ls=':')
    ax.plot([38.0, 42.0], [31.0, 31.0], color=c_reject, lw=1.6, ls=':')
    ax.annotate("", xy=(42.0, 27.0), xytext=(42.0, 31.0),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_reject, ls=':'))
    ax.text(36.0, 33.0, "Budget Exhausted (STATUS_FAILED)", fontsize=6.8,
            color=c_reject, fontweight='bold', ha='right', va='center')

    # Node 7 -> Node 11 (Terminal Outcome: Success, Blocked, or Constraint Failed)
    ax.annotate("", xy=(70.75, 27.0), xytext=(70.75, 43.0),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_success))
    ax.text(71.8, 35.0, "Terminal Outcome:\nSTATUS_SUCCESS,\nSTATUS_BLOCKED, or\nSTATUS_FAILED",
            fontsize=7.2, color='#135200', fontweight='bold', va='center', ha='left', linespacing=1.2)

    # =========================================================================
    # Node 11: memory_governance_node (Spacious, elegant container)
    # Spans x: 33.0 to 86.0 (w=53.0), y: 7.0 to 27.0 (h=20.0)
    # =========================================================================
    box11 = patches.FancyBboxPatch((33.0, 7.0), 53.0, 20.0, boxstyle="round,pad=0.6,rounding_size=1.5",
                                   facecolor=c_gov_bg, edgecolor=c_gov_border, linewidth=2.2)
    ax.add_patch(box11)
    ax.text(59.5, 24.8, "Node 11: memory_governance_node", ha='center', va='center',
            fontsize=10.2, fontweight='bold', color='#135200')
    ax.text(59.5, 22.8, "Closed-Loop Governance Engine (Terminal State Processing)", ha='center', va='center',
            fontsize=8.0, style='italic', color='#333333')

    # Internal sub-panel: REINFORCEMENT BRANCH
    p_left = patches.FancyBboxPatch((34.8, 8.8), 24.5, 12.2, boxstyle="round,pad=0.3,rounding_size=0.8",
                                    facecolor='#ffffff', edgecolor='#a0d911', lw=1.2)
    ax.add_patch(p_left)
    ax.text(47.05, 18.8, "REINFORCEMENT BRANCH", fontsize=7.8, fontweight='bold', color='#135200', ha='center')
    ax.text(47.05, 16.3, "Applied Memory Present (M_applied)", fontsize=7.0, color='#333333', ha='center')
    ax.text(47.05, 13.9, "Escalate: C_{t+1} = C_t + alpha*(1 - C_t)", fontsize=7.0, color='#0050b3', fontweight='bold', ha='center')
    ax.text(47.05, 11.5, "Suppress New Admission (Mutual Exclusion)", fontsize=6.8, color='#555555', style='italic', ha='center')

    # Internal sub-panel: ADMISSION & QUARANTINE BRANCH
    p_right = patches.FancyBboxPatch((60.5, 8.8), 24.0, 12.2, boxstyle="round,pad=0.3,rounding_size=0.8",
                                     facecolor='#ffffff', edgecolor='#a0d911', lw=1.2)
    ax.add_patch(p_right)
    ax.text(72.5, 18.8, "ADMISSION & INTEGRITY BRANCH", fontsize=7.8, fontweight='bold', color='#135200', ha='center')
    ax.text(72.5, 16.3, "Success without Prior Memory & Retries > 0", fontsize=7.0, color='#333333', ha='center')
    ax.text(72.5, 13.9, "Gate: Utility_0 >= 0.25 -> NEW State", fontsize=7.0, color='#389e0d', fontweight='bold', ha='center')
    ax.text(72.5, 11.5, "Blocked / Constraint Failed -> Zero Admission", fontsize=6.8, color='#cf1322', style='italic', ha='center')

    # Terminal Exit Arrow to Final Output (from Node 11 right edge x=86.0 to Final Output)
    ax.annotate("", xy=(89.5, 17.0), xytext=(86.0, 17.0),
                arrowprops=dict(arrowstyle="->", lw=2.0, color=c_edge))
    
    # Final Output Box: comfortably within canvas margins (spans x: 89.5 to 98.5)
    out_box = patches.FancyBboxPatch((89.5, 14.0), 9.0, 6.0, boxstyle="round,pad=0.4,rounding_size=1.0",
                                     facecolor='#ffffff', edgecolor='#666666', linewidth=1.4)
    ax.add_patch(out_box)
    ax.text(94.0, 17.0, "Final Output\n(Result / Status)", ha='center', va='center',
            fontsize=8.0, fontweight='bold', color='#111111', linespacing=1.2)

    plt.tight_layout()
    plt.savefig('manuscript/figures/png/fig1_architecture.png', dpi=300, bbox_inches='tight')
    plt.savefig('manuscript/figures/svg/fig1_architecture.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("Fig 1 (11-Node Architecture) generated successfully: PNG and SVG.")

if __name__ == '__main__':
    generate_fig1()
