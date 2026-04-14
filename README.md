# 🚀 Vertex OAI Python Gateway

<p align="center">
  <a href="./README_EN.md">English Version</a> |
  <b>中文说明</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

这是一个为 **Google Cloud Vertex AI (Gemini 模型)** 提供的 OpenAI 兼容网关。

### 💡 项目背景

本项目参考并改进了 [Gallentboy/vertex-oai](https://github.com/Gallentboy/vertex-oai.git)。原项目在使用 `gemini-3-flash-preview` 等最新模型时可能会遇到 `thought_signature` 缺失导致的 400 错误。本仓库使用 Python 重写，并集成了 `litellm` 作为转换层，完美解决了兼容性问题。

<details>
<summary><b>查看已知错误日志示例</b></summary>

```log
原因: OAI Compatible API error: [400] Bad Request [{ "error": { "code": 400, "message": "Unable to submit request because function call create_file in the 5. content block is missing a thought_signature..." } }]
```
</details>

---

## ✨ 功能特性

-   ✅ **OpenAI API 全兼容**: 完美对接 `/v1/models` 和 `/v1/chat/completions`。
-   ☁️ **Vertex AI 原生集成**: 基于 `google-cloud-aiplatform` 和 `litellm`。
-   👻 **守护进程支持**: 支持类 Unix 系统的后台运行模式。
-   ⚡ **高效缓存**: 自动缓存可用模型列表，减少 API 调用延迟。
-   🌊 **流式输出**: 完整支持 SSE (Server-Sent Events) 流式补全。
-   🧩 **字段保留**: 特别保留了 `thought_signatures` 等高级字段，确保与 GitHub Copilot 的深度兼容。
-   🛠️ **现代技术栈**: 采用 FastAPI + Uvicorn + Python 3.13。

## 📂 项目结构

```text
project root folder
├── py_src/          # 核心 Python 源代码
│   ├── app.py       # FastAPI 路由与业务逻辑
│   ├── config.py    # 配置加载与解析
│   └── main.py      # CLI 命令行入口
├── src/             # (实验性) Rust 实现版本
├── config.yaml      # 全局配置文件
├── main.py          # 项目快速启动入口
└── test_api.py      # API 自动化测试脚本
```

## ⚙️ 配置说明

编辑 `config.yaml`，填入您的 Google Cloud 项目信息。完整的配置项说明如下：

```yaml
vertex_settings:
  project: "your-gcp-project-id"  # 必填：您的 GCP 项目 ID
  location: "global"             # 必填：您的 GCP 区域（如 us-central1 或 global）

server:
  host: "0.0.0.0"                # 监听地址
  port: 8878                     # 监听端口
  debug: false                   # 是否开启调试模式（记录详细的请求/响应日志）
  log_to_file: true              # 是否将日志写入文件
  max_log_lines: 10000           # 日志文件最大保留行数（自动清理）
```

### 🔐 身份验证

在使用本项目前，请确保您拥有访问 Vertex AI 的权限。推荐以下两种方式：
1. **本地开发**：安装 Google Cloud SDK 并运行 `gcloud auth application-default login`。
2. **服务器部署**：创建 Service Account，下载 JSON 密钥并设置环境变量 `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"`。

## 🚀 快速开始

本项目推荐使用 [uv](https://github.com/astral-sh/uv) 进行极速依赖管理。

```bash
# 1. 安装依赖
uv sync

# 2. 激活环境
source .venv/bin/activate

# 3. 启动服务
python main.py start
```

## 🛠️ 常用命令

| 命令 | 说明 |
| :--- | :--- |
| `python main.py start` | 启动服务器（默认后台运行） |
| `python main.py start --foreground` | 在前台启动（方便调试） |
| `python main.py stop` | 停止后台服务器 |
| `python main.py restart` | 重启服务 |
| `python main.py status` | 查看运行状态 |

## 🧪 接口测试

运行以下脚本快速验证服务是否正常：

```bash
python test_api.py
```

## 🚢 部署建议

在生产环境中，请确保已正确配置 GCP 身份验证：
-   设置环境变量 `GOOGLE_APPLICATION_CREDENTIALS` 指向您的 Service Account JSON。
-   或者在服务器上运行 `gcloud auth application-default login`。

---

<p align="center">Made with ❤️ for the AI Community</p>
