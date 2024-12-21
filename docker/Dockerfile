FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装基础工具
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements
COPY docker/requirements.txt /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . /app/

# 创建输出目录
RUN mkdir -p /app/output_docs

# 确保entrypoint脚本可执行
RUN chmod +x /app/docker/entrypoint.sh

# 设置环境变量
ENV PYTHONPATH=/app
ENV OPENAI_API_KEY="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"
ENV OPENAI_MODEL="gpt-4o-mini"

# 设置entrypoint
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["python", "examples/create_document.py"]

