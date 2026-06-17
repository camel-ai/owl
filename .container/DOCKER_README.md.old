# OWL项目Docker使用指南

本文档提供了如何使用Docker运行OWL项目的详细说明。

## 前提条件

- 安装 [Docker](https://docs.docker.com/get-docker/)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/) (推荐v2.x版本)
- 获取必要的API密钥（OpenAI API等）

## 技术说明

本Docker配置使用了以下技术来确保OWL项目在容器中正常运行：

- **Xvfb**：虚拟帧缓冲区，用于在无显示器的环境中模拟X服务器
- **Playwright**：用于自动化浏览器操作，配置为无头模式
- **共享内存**：增加了共享内存大小，以提高浏览器性能
- **BuildKit**：使用Docker BuildKit加速构建过程
- **缓存优化**：使用持久化卷缓存pip和Playwright依赖
- **跨平台兼容**：提供了适用于Windows和macOS/Linux的脚本

## Docker Compose版本说明

本项目使用的docker-compose.yml文件兼容Docker Compose v2.x版本。如果您使用的是较旧的Docker Compose v1.x版本，可能需要手动添加版本号：

```yaml
version: '3'

services:
  # ...其余配置保持不变
```

## 快速开始

### 0. 检查环境

首先，运行检查脚本确保您的环境已准备好：

#### 在macOS/Linux上检查

```bash
# 先给脚本添加执行权限
chmod +x check_docker.sh

# 运行检查脚本
./check_docker.sh
```

#### 在Windows上检查

```cmd
check_docker.bat
```

如果检查脚本发现任何问题，请按照提示进行修复。

### 1. 配置环境变量

复制环境变量模板文件并填写必要的API密钥：

```bash
cp owl/.env_template owl/.env
```

然后编辑 `owl/.env` 文件，填写必要的API密钥，例如：

```
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id
```

### 2. 快速构建Docker镜像

#### 在macOS/Linux上构建

使用提供的Shell脚本，可以加速Docker镜像的构建：

```bash
# 先给脚本添加执行权限
chmod +x build_docker.sh

# 运行构建脚本
./build_docker.sh
```

#### 在Windows上构建

使用提供的批处理文件：

```cmd
build_docker.bat
```

或者使用标准方式构建并启动：

```bash
# 使用BuildKit加速构建
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1
docker-compose build --build-arg BUILDKIT_INLINE_CACHE=1

# 启动容器
docker-compose up -d
```

### 3. 交互式使用容器

容器启动后，会自动进入交互式shell环境，并显示欢迎信息和可用脚本列表：

```bash
# 进入容器（如果没有自动进入）
docker-compose exec owl bash
```

在容器内，您可以直接运行任何可用的脚本：

```bash
# 运行默认脚本
xvfb-python run.py

# 运行DeepSeek示例
xvfb-python run_deepseek_example.py

# 运行脚本并传递查询参数
xvfb-python run.py "什么是人工智能？"
```

### 4. 使用外部脚本运行查询

#### 在macOS/Linux上运行

```bash
# 先给脚本添加执行权限
chmod +x run_in_docker.sh

# 默认使用 run.py 脚本
./run_in_docker.sh "你的问题"

# 指定使用特定脚本
./run_in_docker.sh run_deepseek_example.py "你的问题"
```

#### 在Windows上运行

```cmd
REM 默认使用 run.py 脚本
run_in_docker.bat "你的问题"

REM 指定使用特定脚本
run_in_docker.bat run_deepseek_example.py "你的问题"
```

**可用脚本**：
- `run.py` - 默认脚本，使用OpenAI GPT-4o模型
- `run_deepseek_example.py` - 使用DeepSeek模型
- `run_gaia_roleplaying.py` - GAIA基准测试脚本

## 目录挂载

Docker Compose配置中已经设置了以下挂载点：

- `./owl/.env:/app/owl/.env`：挂载环境变量文件，方便修改API密钥
- `./data:/app/data`：挂载数据目录，用于存储和访问数据文件
- `playwright-cache`：持久化卷，用于缓存Playwright浏览器
- `pip-cache`：持久化卷，用于缓存pip包

## 环境变量

您可以通过以下两种方式设置环境变量：

1. 修改 `owl/.env` 文件
2. 在 `docker-compose.yml` 文件的 `environment` 部分添加环境变量

## 构建优化

本Docker配置包含多项构建优化：

1. **使用国内镜像源**：使用清华大学镜像源加速pip包下载
2. **层优化**：减少Dockerfile中的层数，提高构建效率
3. **缓存利用**：
   - 启用pip缓存，避免重复下载依赖包
   - 使用Docker BuildKit内联缓存
   - 合理安排Dockerfile指令顺序，最大化利用缓存
4. **BuildKit**：启用Docker BuildKit加速构建
5. **持久化缓存**：
   - 使用Docker卷缓存pip包（`pip-cache`）
   - 使用Docker卷缓存Playwright浏览器（`playwright-cache`）
   - 本地缓存目录（`.docker-cache`）

### 缓存清理

如果需要清理缓存，可以使用以下命令：

```bash
# 清理Docker构建缓存
docker builder prune

# 清理Docker卷（会删除所有未使用的卷，包括缓存卷）
docker volume prune

# 清理本地缓存目录
rm -rf .docker-cache
```

## 跨平台兼容性

本项目提供了适用于不同操作系统的脚本：

1. **检查脚本**：
   - `check_docker.sh`（macOS/Linux）：检查Docker环境
   - `check_docker.bat`（Windows）：检查Docker环境

2. **构建脚本**：
   - `build_docker.sh`（macOS/Linux）：构建Docker镜像
   - `build_docker.bat`（Windows）：构建Docker镜像

3. **运行脚本**：
   - `run_in_docker.sh`（macOS/Linux）：运行Docker容器中的脚本
   - `run_in_docker.bat`（Windows）：运行Docker容器中的脚本

这些脚本会自动检测操作系统类型，并使用适当的命令。

## 故障排除

### 容器无法启动

检查日志以获取更多信息：

```bash
docker-compose logs
```

### API密钥问题

确保您已经在 `owl/.env` 文件中正确设置了所有必要的API密钥。

### Docker Compose警告

如果您看到关于`version`属性过时的警告：

```
WARN[0000] docker-compose.yml: the attribute `version` is obsolete
```

这是因为您使用的是Docker Compose v2.x，它不再需要显式指定版本号。我们已经从配置文件中移除了这个属性，所以您不会再看到这个警告。

### 浏览器相关问题

如果遇到浏览器相关的问题，可以尝试以下解决方案：

1. 确保在Docker容器中使用`xvfb-python`命令运行Python脚本
2. 检查是否正确安装了Xvfb和相关依赖
3. 增加共享内存大小（在docker-compose.yml中已设置为2GB）

### 构建速度慢

如果构建速度慢，可以尝试以下解决方案：

1. 确保启用了Docker BuildKit（`DOCKER_BUILDKIT=1`）
2. 确保启用了pip缓存（已在docker-compose.yml中配置）
3. 使用`--build-arg BUILDKIT_INLINE_CACHE=1`参数构建（已在构建脚本中配置）
4. 如果是首次构建，下载依赖包可能需要较长时间，后续构建会更快

### Windows特有问题

如果在Windows上遇到问题：

1. 确保使用管理员权限运行命令提示符或PowerShell
2. 如果遇到路径问题，尝试使用正斜杠（/）而不是反斜杠（\）
3. 如果遇到Docker Compose命令问题，尝试使用`docker compose`（无连字符）

### 内存不足

如果遇到内存不足的问题，可以在 `docker-compose.yml` 文件中调整资源限制：

```yaml
services:
  owl:
    # 其他配置...
    deploy:
      resources:
        limits:
          cpus: '4'  # 增加CPU核心数
          memory: 8G  # 增加内存限制
```

## 自定义Docker镜像

如果需要自定义Docker镜像，可以修改 `Dockerfile` 文件，然后重新构建：

```bash
# macOS/Linux
./build_docker.sh

# Windows
build_docker.bat
``` 