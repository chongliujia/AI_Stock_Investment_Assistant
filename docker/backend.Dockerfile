FROM ubuntu:22.04

WORKDIR /app

# 设置非交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 配置清华源
RUN sed -i 's/ports.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 安装 Python 和基础依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 配置pip
RUN pip3 config set global.timeout 1000 && \
    pip3 config set global.retries 10 && \
    pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件
COPY docker/requirements.txt .

# 安装Python依赖
RUN pip3 install --no-cache-dir wheel && \
    pip3 install --no-cache-dir -r requirements.txt --timeout 1000

# 复制应用代码
COPY . .

# 设置权限
RUN chmod +x /app/docker/entrypoint.sh

EXPOSE 8000

CMD ["/app/docker/entrypoint.sh", "api"]