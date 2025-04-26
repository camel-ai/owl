FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖，包括 ta-lib 所需的编译工具和依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    gcc \
    g++ \
    make \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 TA-Lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# 复制 requirements.txt
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建日志目录
RUN mkdir -p logs screenshots

# 设置环境变量
ENV PYTHONPATH="${PYTHONPATH}:/app"

# 设置entrypoint脚本
RUN echo '#!/bin/bash\n\
if [ "$1" = "test" ]; then\n\
  python src/main.py --test\n\
elif [ -n "$1" ]; then\n\
  python src/main.py --ticker=$1 --model=${2:-qwen}\n\
else\n\
  python src/main.py --ticker=000001 --model=qwen\n\
fi' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# 设置entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# 默认参数
CMD ["000001", "qwen"] 