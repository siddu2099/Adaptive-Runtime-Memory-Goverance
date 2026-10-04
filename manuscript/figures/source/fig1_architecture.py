"""
Figure 1: End-to-End ARMG Architecture and Closed-Loop State Machine
Canonical 10-node LangGraph execution state machine matching graph/workflow.py.
Corrected with:
- Spacious layout eliminating cramped text in Node 10 and subpanels.
- Clean perimeter loopback routing well outside User Query box (zero crossings).
- Protected AST Guard blocked path routed cleanly through inter-row corridor (zero collision with Node 3).
- Generous padding, margins, and crisp typography adhering to IEEE standards.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_fig1():
    os.makedirs('manuscript/figures/png', exist_ok=True)
    os.makedirs('manuscript/figures/svg', exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(15.5, 9.5), dpi=300)
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
                fontsize=9.2, fontweight='bold', color=title_color)
        ax.text(x + w/2, y + (h - 2.8)/2, subtext, ha='center', va='center',
                fontsize=7.8, color='#333333', linespacing=1.25)

    # =========================================================================
    # ROW 1: GENERATION PIPELINE (y: 72 to 87)
    # Nodes: Node 1 (Introspect), Node 2 (Retrieval), Node 3 (SQL Gen), Node 4 (AST Guard)
    # =========================================================================
    
    # User Query Input Box: positioned comfortably to the left of Node 1
    # Spans roughly x: 4.2 to 12.8, y: 76.5 to 82.5
    q_box = patches.FancyBboxPatch((4.5, 76.5), 8.2, 6.0, boxstyle="round,pad=0.4,rounding_size=1.0",
                                   facecolor='#ffffff', edgecolor='#666666', linewidth=1.4)
    ax.add_patch(q_box)
    ax.text(8.6, 79.5, "User Query\n(Natural Language)", ha='center', va='center',
            fontsize=8.2, fontweight='bold', color='#111111', linespacing=1.2)

    # User Query -> Node 1 arrow
    ax.annotate("", xy=(16.0, 79.5), xytext=(12.7, 79.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 1: introspect_and_prune_node
    draw_node(16.0, 72.0, 14.5, 15.0, "Node 1: Introspect & Prune",
              "Catalog Introspection\nZero-Token Pruning\n(information_schema)", c_node_bg, c_node_border)

    # Node 1 -> Node 2 arrow
    ax.annotate("", xy=(34.0, 79.5), xytext=(30.5, 79.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 2: memory_retrieval_node
    draw_node(34.0, 72.0, 14.5, 15.0, "Node 2: Memory Retrieval",
              "Unit-L2 nomic-embed\nFAISS CPU Search\n(Threshold tau >= 0.50)", c_node_bg, c_node_border)

    # Node 2 -> Node 3 arrow
    ax.annotate("", xy=(52.0, 79.5), xytext=(48.5, 79.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 3: sql_generator_node
    draw_node(52.0, 72.0, 14.5, 15.0, "Node 3: SQL Generator",
              "qwen2.5:7b-instruct\nGreedy Decoding\n(temperature = 0.0)", c_node_bg, c_node_border)

    # Node 3 -> Node 4 arrow
    ax.annotate("", xy=(71.0, 79.5), xytext=(66.5, 79.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 4: ast_guard_node
    draw_node(71.0, 72.0, 15.0, 15.0, "Node 4: AST Guard",
              "SQLGlot Static Parser\nBlocks Non-SELECT\nDDL/DML & Multi-Stmt",
              c_guard_bg, c_guard_border, title_color='#ad6800')

    # =========================================================================
    # ROW 2: EXECUTION, OBSERVATION & DIAGNOSIS (y: 43 to 58)
    # Nodes: Node 8 (Knowledge), Node 7 (Diagnosis), Node 6 (Observation), Node 5 (PG Executor)
    # =========================================================================
    
    # Node 4 -> Node 5 (Valid SELECT Query)
    ax.annotate("", xy=(78.5, 58.0), xytext=(78.5, 72.0),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_success))
    ax.text(79.8, 65.0, "Valid Query\n(SELECT only)", fontsize=7.5, color=c_success,
            fontweight='bold', va='center', ha='left', linespacing=1.2)

    # Node 5: postgres_executor_node (Row 2, far right)
    draw_node(71.0, 43.0, 15.0, 15.0, "Node 5: PG Executor",
              "Physical PostgreSQL 16\nRead-Only Transaction\nCapture Rows / Stderr",
              c_exec_bg, c_exec_border, title_color='#096dd9')

    # Node 4 -> Node 6 (Safety Rejection -> Blocked Observation)
    # Routed cleanly through inter-row corridor (y=64.5), completely avoiding Node 3
    ax.plot([71.0, 68.5], [74.5, 74.5], color=c_reject, lw=1.6, ls='--')
    ax.plot([68.5, 68.5], [74.5, 65.0], color=c_reject, lw=1.6, ls='--')
    ax.plot([68.5, 59.25], [65.0, 65.0], color=c_reject, lw=1.6, ls='--')
    ax.annotate("", xy=(59.25, 58.0), xytext=(59.25, 65.0),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_reject, ls='--'))
    ax.text(64.0, 66.8, "Prohibited Mutation\n(STATUS_BLOCKED)", fontsize=7.2,
            color=c_reject, fontweight='bold', ha='center', va='bottom', linespacing=1.1)

    # Node 5 -> Node 6 (Raw driver execution trace)
    ax.annotate("", xy=(66.5, 50.5), xytext=(71.0, 50.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))
    ax.text(68.75, 52.8, "Driver\nTrace", fontsize=7.0, color='#555555',
            ha='center', va='bottom', linespacing=1.1)

    # Node 6: observation_node (Row 2, col 3)
    draw_node(52.0, 43.0, 14.5, 15.0, "Node 6: Observation",
              "Capture RuntimeObservation\nNormalize Stderr\nPreserve Raw State",
              c_repair_bg, c_repair_border, title_color='#1d39c4')

    # Node 6 -> Node 7 (Execution Failure)
    ax.annotate("", xy=(48.5, 50.5), xytext=(52.0, 50.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_reject))
    ax.text(50.25, 52.5, "Failure", fontsize=7.5, color=c_reject,
            fontweight='bold', ha='center', va='bottom')

    # Node 7: diagnosis_node (Row 2, col 2)
    draw_node(34.0, 43.0, 14.5, 15.0, "Node 7: Diagnosis",
              "Canonical 7-Tier Engine\nExtract Broken Tokens\nCandidate Remapping",
              c_repair_bg, c_repair_border, title_color='#1d39c4')

    # Node 7 -> Node 8 arrow
    ax.annotate("", xy=(30.5, 50.5), xytext=(34.0, 50.5),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_edge))

    # Node 8: knowledge_node (Row 2, col 1)
    draw_node(16.0, 43.0, 14.5, 15.0, "Node 8: Knowledge",
              "Form RuntimeKnowledge\nEvaluate Retry Budget\n(K_max = 3 retries)",
              c_repair_bg, c_repair_border, title_color='#1d39c4')

    # =========================================================================
    # ROW 3: REPAIR LOOP & TERMINAL GOVERNANCE (y: 8 to 27)
    # =========================================================================
    
    # Node 8 -> Node 9 (If K <= 3 retries remaining)
    ax.annotate("", xy=(23.25, 27.0), xytext=(23.25, 43.0),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_loop))
    ax.text(21.8, 35.0, "Retries K <= 3\n(STATUS_RETRYING)", fontsize=7.4,
            color=c_loop, fontweight='bold', va='center', ha='right', linespacing=1.2)

    # Node 9: repair_prompt_node (Row 3, col 1)
    draw_node(16.0, 12.0, 14.5, 15.0, "Node 9: Repair Prompt",
              "Strict Negative Constraints\nDiagnostic Repair Rule\nEnforce Budget Bound",
              c_repair_bg, c_repair_border, title_color='#1d39c4')

    # -------------------------------------------------------------------------
    # Node 9 Loopback to Node 3 (Clean perimeter routing outside User Query)
    # Route: Node 9 left (x=16, y=19.5) -> left to x=1.8 -> up to y=93.5 -> right to x=59.25 -> down to Node 3 top (y=87)
    # User Query box is at x: 4.5 to 12.7, so x=1.8 has a 2.7 unit safety margin!
    # -------------------------------------------------------------------------
    ax.plot([16.0, 1.8], [19.5, 19.5], color=c_loop, lw=1.8)
    ax.plot([1.8, 1.8], [19.5, 93.5], color=c_loop, lw=1.8)
    ax.plot([1.8, 59.25], [93.5, 93.5], color=c_loop, lw=1.8)
    ax.annotate("", xy=(59.25, 87.0), xytext=(59.25, 93.5),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_loop))
    ax.text(32.0, 95.2, "Repair Feedback Loop (Max K = 3 Retries)", fontsize=8.5,
            color=c_loop, fontweight='bold', ha='center', va='bottom')

    # Node 8 -> Node 10 (If Budget Exhausted K > 3)
    # Routes out of Node 8 bottom-right, cleanly into Node 10 left edge
    ax.plot([30.5, 32.5], [45.5, 45.5], color=c_reject, lw=1.6, ls=':')
    ax.plot([32.5, 32.5], [45.5, 20.0], color=c_reject, lw=1.6, ls=':')
    ax.annotate("", xy=(34.0, 20.0), xytext=(32.5, 20.0),
                arrowprops=dict(arrowstyle="->", lw=1.6, color=c_reject, ls=':'))
    ax.text(33.6, 35.0, "Budget Exhausted\n(STATUS_FAILED)", fontsize=7.2,
            color=c_reject, fontweight='bold', ha='left', va='center', linespacing=1.2)

    # Node 6 -> Node 10 (Terminal Outcome: Success or Blocked)
    ax.annotate("", xy=(59.25, 27.0), xytext=(59.25, 43.0),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=c_success))
    ax.text(60.5, 35.0, "Terminal Outcome:\nSTATUS_SUCCESS or\nSTATUS_BLOCKED",
            fontsize=7.4, color='#135200', fontweight='bold', va='center', ha='left', linespacing=1.2)

    # =========================================================================
    # Node 10: memory_governance_node (Spacious, elegant container)
    # Spans x: 34.0 to 85.5 (w=51.5), y: 7.0 to 27.0 (h=20.0)
    # =========================================================================
    box10 = patches.FancyBboxPatch((34.0, 7.0), 51.5, 20.0, boxstyle="round,pad=0.6,rounding_size=1.5",
                                   facecolor=c_gov_bg, edgecolor=c_gov_border, linewidth=2.2)
    ax.add_patch(box10)
    ax.text(59.75, 24.8, "Node 10: memory_governance_node", ha='center', va='center',
            fontsize=10.5, fontweight='bold', color='#135200')
    ax.text(59.75, 22.8, "Closed-Loop Governance Engine (Terminal State Processing)", ha='center', va='center',
            fontsize=8.2, style='italic', color='#333333')

    # Internal sub-panel: REINFORCEMENT BRANCH
    p_left = patches.FancyBboxPatch((35.8, 8.8), 23.5, 12.2, boxstyle="round,pad=0.3,rounding_size=0.8",
                                    facecolor='#ffffff', edgecolor='#a0d911', lw=1.2)
    ax.add_patch(p_left)
    ax.text(47.55, 18.8, "REINFORCEMENT BRANCH", fontsize=8.0, fontweight='bold', color='#135200', ha='center')
    ax.text(47.55, 16.3, "Applied Memory Present (M_applied)", fontsize=7.2, color='#333333', ha='center')
    ax.text(47.55, 13.9, "Escalate: C_{t+1} = C_t + alpha*(1 - C_t)", fontsize=7.2, color='#0050b3', fontweight='bold', ha='center')
    ax.text(47.55, 11.5, "Suppress New Admission (Mutual Exclusion)", fontsize=7.0, color='#555555', style='italic', ha='center')

    # Internal sub-panel: ADMISSION BRANCH
    p_right = patches.FancyBboxPatch((60.4, 8.8), 23.5, 12.2, boxstyle="round,pad=0.3,rounding_size=0.8",
                                     facecolor='#ffffff', edgecolor='#a0d911', lw=1.2)
    ax.add_patch(p_right)
    ax.text(72.15, 18.8, "ADMISSION BRANCH", fontsize=8.0, fontweight='bold', color='#135200', ha='center')
    ax.text(72.15, 16.3, "No Prior Memory & Retries > 0", fontsize=7.2, color='#333333', ha='center')
    ax.text(72.15, 13.9, "Gate: Utility_0 >= 0.25 -> NEW State", fontsize=7.2, color='#389e0d', fontweight='bold', ha='center')
    ax.text(72.15, 11.5, "Blocked / Terminal Fail -> Reject", fontsize=7.0, color='#cf1322', style='italic', ha='center')

    # Terminal Exit Arrow to Final Output (from Node 10 right edge x=85.5 to Final Output)
    ax.annotate("", xy=(89.5, 17.0), xytext=(85.5, 17.0),
                arrowprops=dict(arrowstyle="->", lw=2.0, color=c_edge))
    
    # Final Output Box: comfortably within canvas margins (spans x: 89.5 to 98.2)
    out_box = patches.FancyBboxPatch((89.5, 14.0), 8.7, 6.0, boxstyle="round,pad=0.4,rounding_size=1.0",
                                     facecolor='#ffffff', edgecolor='#666666', linewidth=1.4)
    ax.add_patch(out_box)
    ax.text(93.85, 17.0, "Final Output\n(Result / Status)", ha='center', va='center',
            fontsize=8.2, fontweight='bold', color='#111111', linespacing=1.2)

    plt.tight_layout()
    plt.savefig('manuscript/figures/png/fig1_architecture.png', dpi=300, bbox_inches='tight')
    plt.savefig('manuscript/figures/svg/fig1_architecture.svg', format='svg', bbox_inches='tight')
    plt.close()
    print("Fig 1 generated successfully: PNG and SVG.")

if __name__ == '__main__':
    generate_fig1()

