#!/bin/bash

# 设置配置变量 | Set configuration variables
CACHE_DIR=".docker-cache/pip"
BUILD_ARGS="--build-arg BUILDKIT_INLINE_CACHE=1"
COMPOSE_FILE="docker-compose.yml"
CLEAN_CACHE=0
REBUILD=0
SERVICE=""

# 设置Docker BuildKit环境变量 | Set Docker BuildKit environment variables
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# 解析命令行参数 | Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --clean)
            CLEAN_CACHE=1
            shift
            ;;
        --rebuild)
            REBUILD=1
            shift
            ;;
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --help)
            echo "用法 | Usage: ./build_docker.sh [选项 | options]"
            echo "选项 | Options:"
            echo "  --clean     清理缓存目录 | Clean cache directory"
            echo "  --rebuild   强制重新构建镜像 | Force rebuild image"
            echo "  --service   指定要构建的服务名称 | Specify service name to build"
            echo "  --help      显示此帮助信息 | Show this help message"
            exit 0
            ;;
        *)
            echo "未知选项 | Unknown option: $1"
            echo "使用 --help 查看帮助 | Use --help to see help"
            exit 1
            ;;
    esac
done

# 检测操作系统类型 | Detect operating system type
OS_TYPE=$(uname -s)
echo "检测到操作系统 | Detected OS: $OS_TYPE"

# 检查Docker是否安装 | Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "错误 | Error: Docker未安装 | Docker not installed"
    echo "请先安装Docker | Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker是否运行 | Check if Docker is running
if ! docker info &> /dev/null; then
    echo "错误 | Error: Docker未运行 | Docker not running"
    echo "请启动Docker服务 | Please start Docker service"
    exit 1
fi

# 检查docker-compose.yml文件是否存在 | Check if docker-compose.yml file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "错误 | Error: 未找到$COMPOSE_FILE文件 | $COMPOSE_FILE file not found"
    echo "请确保在正确的目录中运行此脚本 | Please make sure you are running this script in the correct directory"
    exit 1
fi

echo "启用Docker BuildKit加速构建... | Enabling Docker BuildKit to accelerate build..."

# 清理缓存（如果指定） | Clean cache (if specified)
if [ $CLEAN_CACHE -eq 1 ]; then
    echo "清理缓存目录... | Cleaning cache directory..."
    rm -rf "$CACHE_DIR"
fi

# 创建缓存目录 | Create cache directory
mkdir -p "$CACHE_DIR"

# 添加构建时间标记 | Add build time tag
BUILD_TIME=$(date +"%Y%m%d_%H%M%S")
BUILD_ARGS="$BUILD_ARGS --build-arg BUILD_TIME=$BUILD_TIME"

# 获取脚本所在目录 | Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 获取项目根目录（脚本所在目录的父目录） | Get project root directory (parent directory of script directory)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "脚本目录 | Script directory: $SCRIPT_DIR"
echo "项目根目录 | Project root directory: $PROJECT_ROOT"

# 切换到项目根目录 | Change to project root directory
cd "$PROJECT_ROOT"

# 检查Docker Compose命令 | Check Docker Compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo "使用 docker-compose 命令 | Using docker-compose command"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    echo "使用 docker compose 命令 | Using docker compose command"
else
    echo "错误 | Error: 未找到Docker Compose命令 | Docker Compose command not found"
    echo "请安装Docker Compose | Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# 检测CPU核心数，用于并行构建 | Detect CPU cores for parallel build
CPU_CORES=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)
if [ $CPU_CORES -gt 2 ]; then
    PARALLEL_FLAG="--parallel"
    echo "检测到${CPU_CORES}个CPU核心，启用并行构建... | Detected ${CPU_CORES} CPU cores, enabling parallel build..."
else
    PARALLEL_FLAG=""
fi

# 构建命令基础部分 | Base part of build command
BUILD_CMD="$COMPOSE_CMD -f \"$SCRIPT_DIR/docker-compose.yml\" build $PARALLEL_FLAG --build-arg BUILDKIT_INLINE_CACHE=1"

# 根据操作系统类型执行不同的命令 | Execute different commands based on OS type
if [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS
    echo "在macOS上构建Docker镜像... | Building Docker image on macOS..."
    eval $BUILD_CMD
elif [[ "$OS_TYPE" == "Linux" ]]; then
    # Linux
    echo "在Linux上构建Docker镜像... | Building Docker image on Linux..."
    eval $BUILD_CMD
elif [[ "$OS_TYPE" == MINGW* ]] || [[ "$OS_TYPE" == CYGWIN* ]] || [[ "$OS_TYPE" == MSYS* ]]; then
    # Windows
    echo "在Windows上构建Docker镜像... | Building Docker image on Windows..."
    eval $BUILD_CMD
else
    echo "未知操作系统，尝试使用标准命令构建... | Unknown OS, trying to build with standard command..."
    eval $BUILD_CMD
fi

# 检查构建结果 | Check build result
if [ $? -eq 0 ]; then
    echo "Docker镜像构建成功！ | Docker image build successful!"
    echo "构建时间 | Build time: $BUILD_TIME"
    echo "可以使用以下命令启动容器： | You can use the following command to start the container:"
    echo "$COMPOSE_CMD -f \"$SCRIPT_DIR/docker-compose.yml\" up -d"
else
    echo "Docker镜像构建失败，请检查错误信息。 | Docker image build failed, please check error messages."
    exit 1
fi