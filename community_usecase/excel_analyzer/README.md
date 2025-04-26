# Excel Analyzer  
[中文](README_zh.md)

This project uses **Owl** for data analysis and visualization.

## Features

- Provides both English and Chinese versions of the raw data and prompts
- Utilizes **CodeExecutionToolkit**, **ExcelToolkit**, and **FileWriteToolkit** to complete related tasks  
- Implements **ExcelRolePlaying** based on **OwlRolePlaying**, which overrides the `system_prompt` with a cleaner, more focused version tailored for data analysis scenarios  
- tested using `gpt-4o` and `deepseek-v3`
- The analysis and visualization of this Excel file involve:
    - Complex headers (merged rows)
    - Nan value handling
    - Complex group calculations
    - Visualization

## How to Use  
1. Set up the environment according to Owl's official instructions
2. Run the following commands:  
    ```bash
    cd community_usecase/excel_analyzer

    # Chinese version, using deepseek-v3
    python excel_analyzer_zh.py

    # English version, using gpt-4o
    python excel_analyzer_zh.py
    ```
3. The analysis results will be saved in the current directory


