FROM node:18-alpine

WORKDIR /app

# 安装基础工具
RUN apk add --no-cache bash netcat-openbsd

# 复制入口脚本并设置权限
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

# 设置工作目录
WORKDIR /app/frontend

# 复制package.json和package-lock.json
COPY frontend/package*.json ./

# 安装依赖
RUN npm install

# 复制其他前端文件
COPY frontend .

# 设置权限
RUN chmod +x /app/frontend/node_modules/.bin/*

EXPOSE 5173

CMD ["/app/docker/entrypoint.sh", "frontend"] 