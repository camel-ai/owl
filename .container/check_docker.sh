#!/bin/bash

# 检测操作系统类型 | Detect operating system type
OS_TYPE=$(uname -s)
echo "检测到操作系统 | Detected OS: $OS_TYPE"

# 检查Docker是否安装 | Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "错误 | Error: Docker未安装 | Docker not installed"
    
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        echo "在macOS上安装Docker的方法 | How to install Docker on macOS:"
        echo "1. 访问 | Visit https://docs.docker.com/desktop/install/mac-install/ 下载Docker Desktop | to download Docker Desktop"
        echo "2. 安装并启动Docker Desktop | Install and start Docker Desktop"
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        echo "在Linux上安装Docker的方法 | How to install Docker on Linux:"
        echo "1. 运行以下命令 | Run the following commands:"
        echo "   sudo apt-get update"
        echo "   sudo apt-get install docker.io docker-compose"
        echo "2. 启动Docker服务 | Start Docker service:"
        echo "   sudo systemctl start docker"
        echo "   sudo systemctl enable docker"
    elif [[ "$OS_TYPE" == MINGW* ]] || [[ "$OS_TYPE" == CYGWIN* ]] || [[ "$OS_TYPE" == MSYS* ]]; then
        echo "在Windows上安装Docker的方法 | How to install Docker on Windows:"
        echo "1. 访问 | Visit https://docs.docker.com/desktop/install/windows-install/ 下载Docker Desktop | to download Docker Desktop"
        echo "2. 安装并启动Docker Desktop | Install and start Docker Desktop"
    fi
    
    exit 1
fi

echo "Docker已安装 | Docker is installed"

# 检查Docker Compose是否安装 | Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "错误 | Error: Docker Compose未安装 | Docker Compose not installed"
    
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        echo "Docker Desktop for Mac已包含Docker Compose | Docker Desktop for Mac already includes Docker Compose"
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        echo "在Linux上安装Docker Compose的方法 | How to install Docker Compose on Linux:"
        echo "1. 运行以下命令 | Run the following command:"
        echo "   sudo apt-get install docker-compose"
    elif [[ "$OS_TYPE" == MINGW* ]] || [[ "$OS_TYPE" == CYGWIN* ]] || [[ "$OS_TYPE" == MSYS* ]]; then
        echo "Docker Desktop for Windows已包含Docker Compose | Docker Desktop for Windows already includes Docker Compose"
    fi
    
    exit 1
fi

echo "Docker Compose已安装 | Docker Compose is installed"

# 检查Docker是否正在运行 | Check if Docker is running
if ! docker info &> /dev/null; then
    echo "错误 | Error: Docker未运行 | Docker not running"
    
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        echo "请启动Docker Desktop应用程序 | Please start Docker Desktop application"
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        echo "请运行以下命令启动Docker服务 | Please run the following command to start Docker service:"
        echo "sudo systemctl start docker"
    elif [[ "$OS_TYPE" == MINGW* ]] || [[ "$OS_TYPE" == CYGWIN* ]] || [[ "$OS_TYPE" == MSYS* ]]; then
        echo "请启动Docker Desktop应用程序 | Please start Docker Desktop application"
    fi
    
    exit 1
fi

echo "Docker正在运行 | Docker is running"

# 检查是否有足够的磁盘空间 | Check if there is enough disk space
FREE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
echo "可用磁盘空间 | Available disk space: $FREE_SPACE"

# 检查是否有.env文件 | Check if .env file exists
if [ ! -f "../owl/.env" ]; then
    echo "警告 | Warning: 未找到../owl/.env文件 | ../owl/.env file not found"
    echo "请运行以下命令创建环境变量文件 | Please run the following command to create environment variable file:"
    echo "cp ../owl/.env_template ../owl/.env"
    echo "然后编辑../owl/.env文件，填写必要的API密钥 | Then edit ../owl/.env file and fill in necessary API keys"
else
    echo "环境变量文件已存在 | Environment variable file exists"
fi

echo "所有检查完成，您的系统已准备好构建和运行OWL项目的Docker容器 | All checks completed, your system is ready to build and run OWL project Docker container"
echo "请运行以下命令构建Docker镜像 | Please run the following command to build Docker image:"

if [[ "$OS_TYPE" == MINGW* ]] || [[ "$OS_TYPE" == CYGWIN* ]] || [[ "$OS_TYPE" == MSYS* ]]; then
    echo "build_docker.bat"
else
    echo "./build_docker.sh"
fi