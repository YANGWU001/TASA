import matplotlib.pyplot as plt

# 确保使用 mathtext（无需系统 LaTeX）
plt.rcParams['text.usetex'] = False

# ------- 数据 -------
dialogue_turns = [0, 4, 8, 12, 16, 20, 24, 28]
# Vanilla-ICL
low_level_1 = [0.00, 32.57, 38.71, 49.90, 42.29, 48.86, 43.19, 47.29]

# TutorLLM
med_level_1  = [0.00, 54.29, 48.10, 54.90, 50.71, 53.57, 58.57, 54.29]

# TASA
high_level_1 = [0.00, 47.90, 44.19, 54.67, 42.19, 51.43, 50.14, 46.10]

lambda_values = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]

# 按百分比填入（表格中的小数 × 100）
red_acc_1   = [48.95, 44.43, 50.00, 54.05, 50.62, 48.57, 59.52]  # GPT
blue_acc_1  = [47.14, 47.62, 45.62, 47.19, 59.67, 54.05, 47.76]  # QWEN
green_acc_1 = [45.14, 50.38, 42.52, 59.19, 50.29, 56.67, 57.52]  # LLAMA


# ------- 画布与子图 -------
fig, axes = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={'wspace': 0.25})

# ------- 左图：Round vs Δ-NLG -------
ax = axes[0]
l1, = ax.plot(dialogue_turns, low_level_1,  marker='o', linewidth=2, markersize=8, label='Low-level')
l2, = ax.plot(dialogue_turns, med_level_1,  marker='s', linewidth=2, markersize=8, label='Med-level')
l3, = ax.plot(dialogue_turns, high_level_1, marker='^', linewidth=2, markersize=8, label='High-level')

ax.set_title(r'Impact of Dialogue Rounds', fontsize=16)
ax.set_xlabel('Dialogue Round', fontsize=14)
ax.set_ylabel(r'$\Delta$-NLG (%)', fontsize=14)
ax.set_xlim(-2.5, 30.5)
ax.set_ylim(0, 62)
ax.set_xticks(dialogue_turns)  # ✅ x 轴刻度对齐到数据点
ax.grid(True, alpha=0.3, linestyle=':', color='gray')

ax.legend(
    handles=[l1, l2, l3],
    labels=['PSS-MV (Llama3.1-8B-Instruct)', 'TutorLLM (Llama3.1-8B-Instruct)', 'TASA (Llama3.1-8B-Instruct)'],
    loc='lower right', fontsize=11, framealpha=0.95
)

for side in ['top', 'right', 'left', 'bottom']:
    ax.spines[side].set_visible(True)
    ax.spines[side].set_linewidth(1.5)

# ------- 右图：λ vs Δ-NLG -------
ax = axes[1]
h1, = ax.plot(lambda_values, red_acc_1,   marker='o', linewidth=2, markersize=8)
h2, = ax.plot(lambda_values, blue_acc_1,  marker='s', linewidth=2, markersize=8)
h3, = ax.plot(lambda_values, green_acc_1, marker='^', linewidth=2, markersize=8)

ax.set_title(r'Impact of $\mathrm{\lambda}$', fontsize=16)
ax.set_xlabel(r'$\mathrm{\lambda}$', fontsize=14)
ax.set_ylabel(r'$\Delta$-NLG (%)', fontsize=14)
ax.set_xlim(-0.1, 1.1)
ax.set_ylim(40, 62)
ax.set_xticks(lambda_values)  # ✅ x 轴刻度对齐到 λ 列表
ax.grid(True, alpha=0.3, linestyle=':', color='gray')

ax.legend(
    handles=[h1, h2, h3],
    labels=['TASA (gpt-oss-120b)', 'TASA (Qwen3-4B-Instruct)', 'TASA (Llama3.1-8B-Instruct)'],
    loc='lower right', fontsize=11, framealpha=0.95
)

for side in ['top', 'right', 'left', 'bottom']:
    ax.spines[side].set_visible(True)
    ax.spines[side].set_linewidth(1.5)

# ------- 导出 -------
plt.tight_layout()
plt.savefig('round_lambda_deltaNLG_side_by_side.png', dpi=300, bbox_inches='tight')
plt.show()
