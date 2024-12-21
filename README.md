# open_multi-agent_framework

## How to start
```
#在根目录下
1. 构建Docker镜像
docker-compose build
2. 运行容器
export OPENAI_API_KEY=your_api_key_here
docker-compose up
or
docker build -t document_agent -f docker/Dockerfile .
docker run -e OPENAI_API_KEY=your_api_key_here -v $(pwd)/output_docs:/app/output_docs document_agent

```


## source code
```
project_root/
├─ docker/
│  ├─ Dockerfile               # 基于Linux镜像的基础环境
│  ├─ requirements.txt         # Python依赖
│  ├─ entrypoint.sh            # 容器启动脚本
│  └─ ...
│
├─ core/
│  ├─ base_agent.py            # Agent抽象基类定义
│  ├─ orchestrator_interface.py# Orchestrator抽象接口定义
│  ├─ task_definition.py       # 定义任务格式与schema
│  ├─ plugin_interface.py      # 插件（扩展）接口定义（可用于添加新Agent或工具）
│  ├─ ...
│
├─ orchestrator/
│  ├─ orchestrator.py          # 默认的Orchestrator实现
│  ├─ orchestrator_config.py   # 配置（如使用哪种LLM、消息队列等）
│  ├─ plugin_manager.py        # 动态加载Agent及扩展插件的机制
│  └─ ...
│
├─ agents/
│  ├─ document_agent.py        # 文档处理智能体
│  ├─ terminal_agent.py        # 终端执行智能体
│  ├─ gui_agent.py             # GUI自动化智能体
│  ├─ llm_agent.py             # LLM驱动的智能体
│  ├─ web_scrape_agent.py      # 网络爬虫Agent（示例）
│  └─ __init__.py
│
├─ llm_providers/
│  ├─ base_llm.py              # 抽象的LLM Provider接口
│  ├─ openai_llm.py            # OpenAI API接入
│  ├─ qwen_llm.py              # Qwen接入（未来扩展）
│  ├─ volcano_llm.py           # 火山大模型接入（未来扩展）
│  ├─ huggingface_llm.py       # Hugging Face模型接入（本地部署或API）
│  ├─ provider_registry.py     # 动态选择LLM Provider的注册表
│  └─ __init__.py
│
├─ plugins/
│  ├─ agent_plugins/           # 可选：第三方agent插件目录
│  ├─ tool_plugins/            # 可选：第三方工具插件（如与Slack通信、访问DB等）
│  └─ ...
│
├─ config/
│  ├─ settings.yaml            # 通用配置（LLM默认选择、日志级别等）
│  ├─ credentials.yaml         # API Key与密钥（或用环境变量）
│  ├─ logging.conf             # 日志配置
│  └─ ...
│
├─ scripts/
│  ├─ run_tasks.py             # 从JSON/YAML文件加载任务的示例运行脚本
│  ├─ interactive_shell.py     # 一个可交互的命令行界面，与Orchestrator交互
│  ├─ deploy.sh                # 部署脚本（Docker构建与运行）
│  └─ ...
│
├─ tests/
│  ├─ test_agents.py           # 测试各Agent实现
│  ├─ test_llm_providers.py    # 测试LLM Provider的mock调用
│  ├─ test_orchestrator.py     # 测试Orchestrator任务调度逻辑
│  ├─ test_plugins.py          # 测试插件加载与调用
│  └─ ...
│
├─ requirements.txt
├─ README.md
└─ LICENSE
```

关键设计要点
1. 核心抽象接口（core/）：
```
base_agent.py：定义Agent接口（如execute(task)方法）。所有智能体必须实现该接口，以统一对外调用方式。
orchestrator_interface.py：为Orchestrator定义抽象接口，便于更换Orchestrator实现（如后期从单进程调度换成分布式消息队列调度）。
task_definition.py：定义统一的任务数据结构（JSON Schema或Pydantic模型），确保Agent接收的任务格式统一且可验证。
plugin_interface.py：定义插件加载的协议，允许第三方开发者编写自定义Agent或工具插件，并在运行时动态加载。
```

2. Orchestrator（orchestrator/）：
```
orchestrator.py：实现默认的调度逻辑（顺序执行任务、异常处理、日志记录等）。
plugin_manager.py：用于扫描plugins/目录或从配置中加载外部插件（如pip install的新Agent包），动态注册到Orchestrator的Agent池中。
orchestrator_config.py：提供一种集中管理配置信息的方式（选择默认的LLM、默认Agents等），也支持从settings.yaml加载。
```

3. Agents（agents/）：
```
独立实现不同功能的Agent，例如：
DocumentAgent：处理.docx创建与编辑（使用python-docx或调用LibreOffice）
TerminalAgent：通过subprocess或pexpect执行终端命令
GuiAgent：利用pyautogui、xdotool或Xvfb进行UI自动化
LLMAgent：调用LLM provider完成自然语言任务（如文本总结、对话生成）
WebScrapeAgent：网络抓取网页内容，供其他Agent使用
每个Agent内部逻辑简单、清晰，并严格遵守Agent接口定义。
```

4. LLM Providers（llm_providers/）：

```
base_llm.py：定义LLM Provider抽象类，提供统一的generate、chat等方法。
openai_llm.py、qwen_llm.py、volcano_llm.py、huggingface_llm.py：分别实现对不同平台的调用。
provider_registry.py：提供一个全局注册表，通过名字（如"openai"）选择相应Provider。
LLMAgent在运行时可从provider_registry获取指定的LLM Provider，无需修改Agent本身。
```

5. Plugins（plugins/）：
```
允许第三方开发者将其Agent或工具作为插件加入系统，而无需修改核心代码。
agent_plugins/中可放置自定义Agent的Python包，若实现Agent接口并在plugin_interface.py定义的协议中注册，即可被Orchestrator加载。
tool_plugins/可以是提供给Agent使用的工具类插件，如调用外部API、数据库连接、文件存储系统等。
```

6. Tests（tests/）：
```
对每个模块（Agent、LLM Provider、Orchestrator、Plugins）进行单元测试。
使用mock来测试LLM调用逻辑，避免单元测试时真实调用外部API。
```

7. 部署和运行：
```
docker/目录下的Dockerfile定义了统一的依赖环境（安装Python、所需库、Xvfb环境等）。
scripts/run_tasks.py提供从文件中加载任务并执行的快速演示。
可以通过docker run ...或docker-compose启动，在容器中运行Orchestrator及Agent进行自动化任务。
```

8. 扩展方向
```
分布式多智能体：将Orchestrator改造成一个调度服务，多个Agent在不同容器或机器上运行，通过RabbitMQ、Redis Pub/Sub等消息队列通信。
Web界面与API：在本框架基础上，添加一个api/目录，使用Flask/FastAPI提供HTTP API，用户可通过Web界面输入任务指令并查看执行结果。
权限与安全：对Agent的行为添加权限管理和审计日志，防止自动化助手在无控制的情况下执行风险操作。
```
