FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装基础工具和中文字体
RUN apt-get update && apt-get install -y \
    git \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements
COPY docker/requirements.txt /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . /app/

# 创建输出目录
RUN mkdir -p /app/output_docs

# 设置环境变量
ENV PYTHONPATH=/app
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}

# 开发环境不使用entrypoint
CMD ["python", "examples/create_document.py"]

