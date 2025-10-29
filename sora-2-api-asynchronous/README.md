# Sora-2 API 异步调用完整示例

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![Go](https://img.shields.io/badge/go-1.16+-00ADD8.svg)](https://golang.org/)
[![Node.js](https://img.shields.io/badge/node.js-14+-green.svg)](https://nodejs.org/)
[![Java](https://img.shields.io/badge/java-8+-orange.svg)](https://www.oracle.com/java/)

> 基于 OpenAI Sora-2 模型的视频生成 API 完整异步调用示例，支持多种编程语言实现。

## 📖 项目简介

本项目提供了 Sora-2 视频生成 API 的完整异步调用流程实现，包含从提交请求、轮询状态到下载视频的全自动化流程。支持 Python、Go、Java、JavaScript 和 Bash/Curl 五种语言实现。

### 核心特性

- ✅ **完整异步流程**：自动完成提交→轮询→下载三步流程
- ✅ **多语言支持**：Python、Go、Java、JavaScript、Bash/Curl
- ✅ **智能轮询**：30 秒间隔，避免频繁请求
- ✅ **用户友好**：详细的进度提示和时间预期（3-5 分钟）
- ✅ **错误处理**：完善的异常处理和超时控制
- ✅ **开箱即用**：简单配置即可运行

## 🎬 功能说明

本项目实现了 Sora-2 API 的完整调用流程：

```
┌─────────────────────────────────────────────────────────────┐
│                    Sora-2 异步视频生成流程                    │
└─────────────────────────────────────────────────────────────┘

  第一步：提交请求
  ┌──────────────────────────────────────────┐
  │  POST /v1/videos                         │
  │  - 上传参考图片                            │
  │  - 提供文本描述（prompt）                  │
  │  - 设置分辨率和时长                        │
  └──────────────┬───────────────────────────┘
                 │
                 ▼
         返回 video_id
                 │
                 ▼
  第二步：轮询状态（每 30 秒）
  ┌──────────────────────────────────────────┐
  │  GET /v1/videos/{video_id}               │
  │  - submitted   → 已提交                  │
  │  - in_progress → 生成中（显示进度）        │
  │  - completed   → 生成完成 ✓               │
  │  - failed      → 生成失败 ✗               │
  └──────────────┬───────────────────────────┘
                 │
                 ▼
       等待 3-5 分钟
                 │
                 ▼
  第三步：下载视频
  ┌──────────────────────────────────────────┐
  │  GET /v1/videos/{video_id}/content       │
  │  - 下载 MP4 视频文件                      │
  │  - 显示下载进度                           │
  └──────────────┬───────────────────────────┘
                 │
                 ▼
          保存到本地 🎉
```

## 🚀 快速开始

### 前置要求

- 有效的 Sora-2 API Key（在代码中配置）
- 一张参考图片（PNG/JPG 格式）
- 根据选择的语言安装对应的运行环境

### 安装依赖

根据你选择的语言版本安装相应依赖：

#### Python
```bash
pip install requests
```

#### Node.js
```bash
npm install axios form-data
```

#### Go
```bash
# 无需额外依赖，使用标准库
go mod init sora-2-async
```

#### Java
```bash
# 下载 org.json 库
wget https://repo1.maven.org/maven2/org/json/json/20240303/json-20240303.jar
```

#### Bash/Curl
```bash
# 系统自带，无需安装
```

### 配置参数

在运行前，需要修改代码中的以下配置：

```python
# 所有语言版本都需要配置这些参数
API_KEY = "sk-your-api-key-here"              # 替换为你的 API Key
IMAGE_PATH = "/path/to/your/image.png"         # 替换为你的图片路径
PROMPT = "详细的视频描述"                        # 替换为你的视频描述
```

### 运行示例

#### Python 版本
```bash
python sora-2-complete-async.py
```

#### Bash/Curl 版本
```bash
chmod +x sora-2-complete-async.sh
./sora-2-complete-async.sh
```

#### Go 版本
```bash
go run sora-2-complete-async.go
# 或编译后运行
go build sora-2-complete-async.go
./sora-2-complete-async
```

#### Java 版本
```bash
javac -cp json-20240303.jar Sora2CompleteAsync.java
java -cp .:json-20240303.jar Sora2CompleteAsync
```

#### JavaScript/Node.js 版本
```bash
node sora-2-complete-async.js
```

## 📁 项目结构

```
sora-2-api-asynchronous/
├── README.md                           # 项目说明文档（本文件）
├── API-MANUAL.md                       # 完整 API 手册
├── knowledge-base.md                   # 需求文档
│
├── sora-2-complete-async.py            # Python 完整实现
├── sora-2-complete-async.sh            # Bash/Curl 完整实现
├── sora-2-complete-async.go            # Go 完整实现
├── sora-2-complete-async.js            # JavaScript/Node.js 完整实现
├── Sora2CompleteAsync.java             # Java 完整实现
│
└── sora-2-yibu-video_request.py        # 原始 Python 请求示例（仅第一步）
```

## 💻 代码示例

### Python 简化示例

```python
import requests
import time

API_KEY = "sk-your-api-key-here"
BASE_URL = "https://api.apiyi.com/v1/videos"

# 第一步：提交请求
def submit_request():
    with open('image.png', 'rb') as f:
        files = {'input_reference': f}
        data = {
            'prompt': '参考配图，使得动物们活跃起来',
            'model': 'sora-2',
            'size': '1280x720',
            'seconds': '10'
        }
        headers = {'Authorization': API_KEY}
        response = requests.post(BASE_URL, headers=headers, data=data, files=files)
        return response.json()['id']

# 第二步：轮询状态
def poll_status(video_id):
    while True:
        response = requests.get(f"{BASE_URL}/{video_id}",
                               headers={'Authorization': API_KEY})
        result = response.json()

        print(f"状态: {result['status']}, 进度: {result.get('progress', 0)}%")

        if result['status'] == 'completed':
            return True
        elif result['status'] == 'failed':
            return False

        time.sleep(30)  # 等待 30 秒

# 第三步：下载视频
def download_video(video_id):
    response = requests.get(f"{BASE_URL}/{video_id}/content",
                           headers={'Authorization': API_KEY})
    with open('video.mp4', 'wb') as f:
        f.write(response.content)

# 执行完整流程
video_id = submit_request()
if poll_status(video_id):
    download_video(video_id)
    print("✅ 视频生成并下载成功！")
```

### Curl 命令行快速测试

```bash
# 1. 提交请求
VIDEO_ID=$(curl -s -X POST "https://api.apiyi.com/v1/videos" \
  -H "Authorization: sk-your-api-key-here" \
  -F "prompt=参考配图，使得动物们活跃起来" \
  -F "model=sora-2" \
  -F "size=1280x720" \
  -F "seconds=10" \
  -F "input_reference=@image.png" \
  | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

echo "视频ID: $VIDEO_ID"

# 2. 查询状态
curl -X GET "https://api.apiyi.com/v1/videos/$VIDEO_ID" \
  -H "Authorization: sk-your-api-key-here"

# 3. 下载视频（等视频完成后）
curl -X GET "https://api.apiyi.com/v1/videos/$VIDEO_ID/content" \
  -H "Authorization: sk-your-api-key-here" \
  -o video.mp4
```

## ⚙️ 配置说明

### 可配置参数

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `API_KEY` | API 认证密钥 | 你的 API Key | 必填 |
| `PROMPT` | 视频描述文本 | 任意文本 | 必填 |
| `IMAGE_PATH` | 参考图片路径 | 本地文件路径 | 必填 |
| `MODEL` | 模型名称 | `sora-2` | `sora-2` |
| `SIZE` | 视频分辨率 | `1280x720`、`720x1280` | `1280x720` |
| `SECONDS` | 视频时长（秒） | `10`、`15` | `10` |
| `POLL_INTERVAL` | 轮询间隔（秒） | 建议 ≥ 30 | `30` |
| `MAX_WAIT_TIME` | 最大等待时间（秒） | 建议 600 | `600` |

### Prompt 编写技巧

好的 Prompt 应该包含：
- **场景描述**：环境、背景、光线
- **主体动作**：明确的动作描述
- **镜头风格**：特写、远景、跟随镜头等
- **艺术风格**：电影感、卡通、写实等

示例：
```
参考配图，一只金毛犬在绿色草地上追逐红色飞盘，阳光明媚，
背景是蓝天白云和绿树，运动流畅，特写镜头跟随犬的动作，
电影级画质，暖色调
```

## 📊 运行输出示例

```
🎬 开始 Sora-2 视频生成完整流程
⏰ 开始时间: 2024-01-01 10:00:00

============================================================
第一步：提交视频生成请求
============================================================
📤 发送请求...
   - 提示词: 参考配图，使得动物们活跃起来，在场地里绕场一周的追逐
   - 图片: /Users/chenkang/Downloads/dog-and-cat.png
   - 尺寸: 1280x720
   - 时长: 10秒
✅ 请求提交成功!
   - 视频ID: video_abc123def456
   - 状态: submitted
   - 创建时间: 2024-01-01 10:00:05
   ⏱️  预计生成时间: 3-5 分钟

============================================================
第二步：查询视频生成状态
============================================================
💡 提示：视频生成通常需要 3-5 分钟，每 30 秒自动查询一次

🔍 查询状态... (已等待 0 秒)
   - 状态: in_progress
   - 进度: 15%
⏳ 视频生成中，等待 30 秒后继续查询...

🔍 查询状态... (已等待 30 秒)
   - 状态: in_progress
   - 进度: 45%
⏳ 视频生成中，等待 30 秒后继续查询...

🔍 查询状态... (已等待 180 秒)
   - 状态: completed
   - 进度: 100%
✅ 视频生成完成!
   - 视频URL: https://api.apiyi.com/v1/videos/video_abc123def456/content
   - 完成时间: 2024-01-01 10:03:25

============================================================
第三步：下载视频
============================================================
📥 开始下载视频...
   下载进度: 100.0% (12456789/12456789 字节)
✅ 视频下载成功!
   - 保存路径: /Users/chenkang/Downloads/sora_video_3def456.mp4
   - 文件大小: 11.88 MB

============================================================
🎉 完整流程执行成功!
============================================================
⏰ 结束时间: 2024-01-01 10:03:50
```

## 🔧 常见问题

### Q1: 视频生成需要多长时间？
**A:** 通常需要 3-5 分钟，具体时间取决于服务器负载和视频复杂度。

### Q2: 为什么我的请求失败了？
**A:** 检查以下几点：
- API Key 是否正确
- 图片文件是否存在且格式正确
- 必填参数是否都已提供
- 网络连接是否正常

### Q3: 可以自定义轮询间隔吗？
**A:** 可以，但建议不要小于 30 秒，频繁请求可能触发速率限制（429 错误）。

### Q4: 视频文件会保存多久？
**A:** 建议视频生成完成后立即下载，避免文件过期。具体保存时长请咨询 API 服务商。

### Q5: 支持批量生成视频吗？
**A:** 本示例是单个视频流程，如需批量生成，可以：
- 串行执行多个请求
- 或同时提交多个请求，分别轮询（注意并发限制）

### Q6: 生成失败如何处理？
**A:** 检查响应中的错误信息，常见原因：
- 内容违规（修改 prompt）
- 配额不足（充值或升级）
- 参数错误（检查参数格式）

## 📚 文档资源

- [API 完整手册](API-MANUAL.md) - 详细的 API 端点说明
- [需求文档](knowledge-base.md) - 项目需求和背景
- [示例代码](#代码示例) - 各语言实现示例

## 🛠️ 技术栈

| 语言 | 版本要求 | 主要库 |
|------|---------|--------|
| Python | 3.7+ | requests |
| Node.js | 14+ | axios, form-data |
| Go | 1.16+ | net/http (标准库) |
| Java | 8+ | org.json |
| Bash | 4.0+ | curl, grep, sed |

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📮 联系方式

- 项目维护者：chenkang
- 技术支持：support@apiyi.com
- API 文档：https://docs.apiyi.com

## ⭐ Star History

如果这个项目对你有帮助，请给一个 Star ⭐️

---

## 🎯 版本更新

### v1.0.0 (2024-01-01)
- ✅ 初始版本发布
- ✅ 支持 Python、Go、Java、JavaScript、Bash 五种语言
- ✅ 完整的异步流程实现
- ✅ 详细的文档和示例

---

**祝你使用愉快！如有问题，欢迎提 Issue 或 PR。** 🎉
