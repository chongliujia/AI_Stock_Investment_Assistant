# AI Workflow System

一个基于AI的工作流系统，支持文档生成和多智能体协作。

## 项目结构

.
├── agents/             # AI智能体实现
├── api/               # FastAPI后端服务
├── core/              # 核心功能模块
├── docker/            # Docker配置文件
├── frontend/          # React前端应用
└── output_docs/       # 生成的文档输出目录

## 使用指南

### 1. 环境配置

1. 复制环境变量模板并设置：

```
cp .env.example .env
```

2. 确保已安装 Docker 和 Docker Compose

### 2. 启动服务

#### 开发环境

```
docker-compose -f docker-compose.dev.yml up
``` 

#### 生产环境

```bash
# 启动生产环境
docker-compose up --build
```

### 3. 访问服务

- 前端界面：http://localhost:5173
- API文档：http://localhost:8000/docs

### 4. 使用工作流编辑器

1. 从左侧面板拖拽智能体节点到工作区
2. 点击节点进行配置（设置提示词、文档类型等）
3. 连接节点形成工作流
4. 点击"执行工作流"按钮运行

### 5. 文档生成

支持生成以下类型的文档：
- 中文/英文报告
- 分析文档
- 研究总结

可配置参数：
- 文档类型
- 字数要求
- 语言选择
- 自定义提示词

生成的文档将保存在 `output_docs` 目录中。

## 开发指南

### 添加新的智能体

1. 在 `agents/` 目录下创建新的智能体类
2. 在 `api/main.py` 中注册新的节点类型
3. 在前端添加对应的节点配置和显示逻辑

### 调试

```bash
# 查看后端日志
docker-compose -f docker-compose.dev.yml logs -f backend

# 查看前端日志
docker-compose -f docker-compose.dev.yml logs -f frontend
```

## 注意事项

1. 确保 API Key 安全性
2. 注意文档生成的字数限制
3. 保持工作流结构清晰
