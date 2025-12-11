# ModelScope 智能路由器

一个基于FastAPI的智能模型路由系统，用于管理和路由多个AI模型的API调用，实现负载均衡和故障转移。

## 功能特点

- 🔄 **智能路由**: 自动选择可用的模型进行API调用
- 📊 **实时监控**: 提供美观的控制台界面，实时显示模型状态和使用情况
- 🚫 **限流检测**: 自动检测并跳过达到API限制的模型
- 📈 **统计分析**: 记录每个模型的调用次数、成功率和响应时间
- 🔄 **故障转移**: 当某个模型调用失败时，自动尝试其他可用模型
- 🌊 **流式支持**: 完全支持流式响应和非流式响应

## 项目结构

```
refactored_router/
├── main.py              # 主应用程序入口
├── settings.py          # 配置管理
├── network.py           # API客户端和网络请求处理
├── stats.py             # 统计数据管理
├── ui.py                # 控制台UI界面
├── schema.py            # 数据模型定义
├── config.json          # 模型配置文件
├── .env                 # 环境变量配置
└── router_data/         # 数据存储目录
    └── model_stats.json # 模型统计数据
```

## 快速开始

### 1. 环境准备

确保你的系统已安装Python 3.8+，然后安装项目依赖：

```bash
pip install fastapi uvicorn httpx rich pydantic
```

### 2. 配置设置

1. 复制并编辑 `.env` 文件：

```env
MS_API_KEY=你的魔搭社区API密钥
MS_BASE_URL=https://api-inference.modelscope.cn/v1
PORT=2166
```

2. 根据需要修改 `config.json` 文件中的模型配置：

```json
[
  {"name": "deepseek-v3-2", "model_id": "deepseek-ai/DeepSeek-V3.2", "estimated_limit": 50},
  {"name": "glm-4-5", "model_id": "ZhipuAI/GLM-4.5", "estimated_limit": 50}
]
```

### 3. 运行服务

```bash
# 在项目根目录下运行
python -m refactored_router.main
```

服务将在 `http://localhost:2166` 启动。

## API使用

### 聊天完成接口

```bash
curl -X POST "http://localhost:2166/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "modelscope-router",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
  }'
```

### 指定模型

你也可以指定具体的模型名称：

```bash
curl -X POST "http://localhost:2166/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-v3-2",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
  }'
```

### 流式响应

```bash
curl -X POST "http://localhost:2166/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "modelscope-router",
    "messages": [
      {"role": "user", "content": "写一个Python函数"}
    ],
    "stream": true
  }'
```

## 控制台界面

服务启动后，你会看到一个实时的控制台界面，显示：

- 📊 每个模型的使用情况（当前调用次数/限制）
- ✅ 成功率统计
- 🔴 模型状态（活跃/受限）
- 📝 实时请求日志
- ⏱️ 响应时间统计

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MS_API_KEY` | 魔搭社区API密钥 | 必填 |
| `MS_BASE_URL` | API基础URL | `https://api-inference.modelscope.cn/v1` |
| `PORT` | 服务端口 | `2166` |

### 模型配置

在 `config.json` 中配置模型：

```json
{
  "name": "模型显示名称",
  "model_id": "模型在ModelScope中的ID",
  "estimated_limit": 每日预估调用限制
}
```

## 工作原理

1. **请求接收**: 接收标准的OpenAI格式的聊天完成请求
2. **模型选择**: 根据配置和统计信息选择可用的模型
3. **负载均衡**: 优先选择调用次数较少的模型
4. **故障转移**: 如果模型调用失败，自动尝试下一个可用模型
5. **统计记录**: 记录每次调用的结果，用于后续决策
6. **限流处理**: 自动检测并跳过达到API限制的模型

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持多模型路由和故障转移
- 实时监控界面
- 统计数据管理