import matplotlib.pyplot as plt

# camel-ai的camel框架GitHub统计信息
data = {'Stars': 15700, 'Forks': 1700}
labels = list(data.keys())
values = list(data.values())

# 创建条形图
plt.bar(labels, values, color=['blue', 'green'])
plt.xlabel('类别')
plt.ylabel('数量')
plt.title('camel-ai/camel GitHub Stars 和 Forks 数目')

# 显示图形
plt.show()