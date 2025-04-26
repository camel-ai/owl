# Excel Analyzer
这个项目使用owl来做数据分析和可视化


## Features
- 提供了英文，中文两个版本的原始数据和prompt，方便理解
- 使用**CodeExecutionToolkit**，**ExcelToolkit**，**FileWriteToolkit**来完成相关工作
- 在**OwlRolePlaying**基础之上实现了**ExcelRolePalying**，它重写了system_prompt，更简洁，聚焦在数据分析场景
- 经过测试，在`gpt-4o`和`deepseek-v3`下均可以达到预期效果
- 对该excel进行分析和可视化时涉及到的内容有：
    - 复杂表头（合并行）
    - 缺失值处理
    - 复杂的分组计算
    - 可视化

## How to use 
1. 按照owl的官方流程搭建好环境
2. 运行
    ```
    cd community_usecase/excel_analyzer

    # Chinese version, using deepseek-v3
    python excel_analyzer_zh.py

    # English version, using gpt-4o
    python excel_analyzer_zh.py
    ```
3. 数据集分析的结果将会在出存在当前目录下


