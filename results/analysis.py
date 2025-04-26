import json
from scipy.stats import ttest_rel

# 工具函数：将 True/False 或 'true'/'false' 转成 1/0
def bool_to_int(val):
    if isinstance(val, bool):
        return int(val)
    return 1 if str(val).lower() == 'true' else 0

# 读取并转换一个文件
def load_scores(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {item['task_id']: bool_to_int(item['score']) for item in data}

# 加载两个结果文件
scores1 = load_scores('./results/result_50samples_forder_owl_agent_prompt_index2.json')
scores2 = load_scores('./results/result.json')

# 构造所有 task_id 的并集
all_ids = sorted(set(scores1.keys()) | set(scores2.keys()))

# 对不存在的 task_id 填 0
vals1 = [scores1.get(tid, 0) for tid in all_ids]
vals2 = [scores2.get(tid, 0) for tid in all_ids]

# 执行配对 t 检验
t_stat, p_value = ttest_rel(vals1, vals2)

print(f'共 {len(all_ids)} 个样本（包含缺失填 0）')
print(f'配对 t 检验: t = {t_stat:.4f}, p = {p_value:.4e}')