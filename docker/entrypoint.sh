#!/bin/bash
set -e

# 检查必要的环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set"
    exit 1
fi

# 执行命令
exec "$@"
