import json
import matplotlib.pyplot as plt
import numpy as np

# 设置颜色
model_colors = {
    'OWL': '#4C72B0',  # 蓝色
    'SEW (OWL)': '#C44E52'   # 红色
}

def load_and_process_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    level_stats = {1: {'total': 0, 'correct': 0},
                   2: {'total': 0, 'correct': 0},
                   3: {'total': 0, 'correct': 0}}
    
    for item in data:
        level = item['level']
        score = item['score']
        correct = 1 if (score is True or score == 1) else 0
        level_stats[level]['total'] += 1
        level_stats[level]['correct'] += correct
    
    level_accuracy = {level: stats['correct']/stats['total'] if stats['total'] > 0 else 0 
                     for level, stats in level_stats.items()}
    
    total_correct = sum(stats['correct'] for stats in level_stats.values())
    total_items = sum(stats['total'] for stats in level_stats.values())
    overall_accuracy = total_correct / total_items if total_items > 0 else 0
    
    return level_accuracy, overall_accuracy

# 加载数据
file2_path = 'results/_allvalid_SEW_forder_index2.json'
file1_path = 'results/_allvalid_original.json'
owl_levels, owl_overall = load_and_process_json(file1_path)
sew_levels, sew_overall = load_and_process_json(file2_path)

# 准备绘图数据（转换为百分比）
categories = ['Level 1', 'Level 2', 'Level 3', 'Overall']
owl_scores = [owl_levels[1]*100, owl_levels[2]*100, owl_levels[3]*100, owl_overall*100]
sew_scores = [sew_levels[1]*100, sew_levels[2]*100, sew_levels[3]*100, sew_overall*100]

# 计算百分比提升
improvements = []
for owl, sew in zip(owl_scores, sew_scores):
    if owl == 0:  # 避免除以零
        improvement = 0
    else:
        improvement = (sew - owl) / owl * 100
    improvements.append(improvement)

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
fig.patch.set_facecolor('#f8f9fa')
ax.set_facecolor('#ffffff')

# 柱状图参数
bar_width = 0.35
x = np.arange(len(categories))

# 绘制OWL
rects1 = ax.bar(x - bar_width/2, owl_scores, bar_width,
                color=model_colors['OWL'], label='OWL (Original)',
                edgecolor='white', linewidth=1, alpha=0.9)

# 绘制SEW (OWL)
rects2 = ax.bar(x + bar_width/2, sew_scores, bar_width,
                color=model_colors['SEW (OWL)'], label='OWL (Optimized)',
                edgecolor='white', linewidth=1, alpha=0.9)

# 添加准确率标签（百分比格式，保留2位小数）
def add_accuracy_labels(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}%',  # 修改为保留2位小数
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9)

add_accuracy_labels(rects1)
add_accuracy_labels(rects2)

# 添加百分比提升标签（保留2位小数）
for i, (imp, sew) in enumerate(zip(improvements, sew_scores)):
    ax.annotate(f'↑{imp:.2f}%',  # 修改为保留2位小数
                xy=(x[i] + bar_width/2, sew),
                xytext=(0, 18),
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=9, color='#C44E52', weight='bold')

# 美化图表
ax.set_ylabel('Accuracy (%)', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=12)
ax.set_ylim(0, 50)
ax.yaxis.grid(True, linestyle=':', alpha=0.7)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 添加图例
ax.legend(frameon=True, facecolor='#ffffff')

plt.tight_layout()
plt.savefig('results/result_comparison_percentage.png', dpi=300, bbox_inches='tight')
# plt.show()
plt.close()