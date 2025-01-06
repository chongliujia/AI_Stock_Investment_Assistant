#!/bin/bash
set -e

# 检查必要的环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set"
    exit 1
fi

# 获取要运行的脚本
SCRIPT=${SCRIPT:-"examples/create_both_documents.py"}

# 执行指定的Python脚本
exec python "$SCRIPT"
