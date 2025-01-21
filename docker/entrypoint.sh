#!/bin/bash
set -e

# 等待依赖的服务就绪
wait_for_service() {
    local host="$1"
    local port="$2"
    local service="$3"
    local retries=30
    
    echo "Waiting for $service to be ready..."
    until nc -z "$host" "$port" > /dev/null 2>&1; do
        retries=$((retries - 1))
        if [ $retries -eq 0 ]; then
            echo >&2 "Error: $service is not available"
            exit 1
        fi
        sleep 1
    done
    echo "$service is ready!"
}

# 检查环境变量
check_env_vars() {
    required_vars=("OPENAI_API_KEY")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "Error: Required environment variable $var is not set"
            exit 1
        fi
    done
}

# 创建必要的目录
setup_directories() {
    mkdir -p "${OUTPUT_DIR:-output_docs}"
    chmod 777 "${OUTPUT_DIR:-output_docs}"
}

# 主函数
main() {
    check_env_vars
    setup_directories
    
    # 根据命令行参数执行不同的操作
    case "$1" in
        "api")
            echo "Starting API server..."
            exec uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
            ;;
        "frontend")
            echo "Starting frontend development server..."
            cd frontend && npm install && npm run dev
            ;;
        *)
            echo "Usage: $0 {api|frontend}"
            exit 1
            ;;
    esac
}

main "$@"
