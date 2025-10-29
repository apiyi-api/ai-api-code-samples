# Sora-2 API 完整手册

## 目录

- [概述](#概述)
- [认证](#认证)
- [基础信息](#基础信息)
- [完整异步流程](#完整异步流程)
- [API 端点详解](#api-端点详解)
  - [1. 提交视频生成请求](#1-提交视频生成请求)
  - [2. 查询视频状态](#2-查询视频状态)
  - [3. 下载视频内容](#3-下载视频内容)
- [状态说明](#状态说明)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)
- [示例代码](#示例代码)

---

## 概述

Sora-2 API 是一个基于 OpenAI Sora 模型的视频生成服务，支持从文本描述和参考图片生成高质量视频。

**核心特性**：
- 文本到视频生成（Text-to-Video）
- 图片参考生成（Image-to-Video）
- 支持多种分辨率（1280x720、720x1280）
- 支持多种时长（10 秒、15 秒）
- 异步处理机制

---

## 认证

所有 API 请求都需要在 HTTP 请求头中包含 API Key：

```http
Authorization: sk-your-api-key-here
```

**获取 API Key**：请联系服务提供商获取您的专属 API Key。

---

## 基础信息

### API 基础 URL

```
https://api.apiyi.com/v1/videos
```

### 支持的参数

| 参数 | 类型 | 必填 | 说明 | 可选值 |
|------|------|------|------|--------|
| `prompt` | string | ✅ | 视频生成的文本描述 | 任意文本 |
| `model` | string | ✅ | 模型名称 | `sora-2` |
| `size` | string | ✅ | 视频分辨率 | `1280x720`、`720x1280` |
| `seconds` | string | ✅ | 视频时长（秒） | `10`、`15` |
| `input_reference` | file | ❌ | 参考图片文件 | PNG、JPG、JPEG |

---

## 完整异步流程

Sora-2 API 采用异步处理机制，完整流程包含三个步骤：

```
第一步：提交请求 → 获取 video_id
    ↓
第二步：轮询查询 → 检查生成状态（submitted → in_progress → completed）
    ↓
第三步：下载视频 → 保存到本地
```

**典型时间线**：
- 请求提交：即时响应（< 1 秒）
- 视频生成：通常 3-5 分钟
- 视频下载：根据网络速度，通常 10-30 秒

**推荐轮询策略**：
- 轮询间隔：30 秒
- 最大等待时间：10 分钟
- 超时后建议重新提交请求

---

## API 端点详解

### 1. 提交视频生成请求

#### 端点

```
POST /v1/videos
```

#### 请求方式

`multipart/form-data`

#### 请求头

```http
Authorization: sk-your-api-key-here
Accept: application/json
```

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 视频生成描述，建议详细描述场景、动作、风格 |
| `model` | string | ✅ | 固定值：`sora-2` |
| `size` | string | ✅ | `1280x720`（横屏）或 `720x1280`（竖屏） |
| `seconds` | string | ✅ | `10` 或 `15` |
| `input_reference` | file | ❌ | 参考图片，支持 PNG/JPG/JPEG，建议 < 10MB |

#### Curl 示例

```bash
curl -X POST "https://api.apiyi.com/v1/videos" \
  -H "Authorization: sk-your-api-key-here" \
  -H "Accept: application/json" \
  -F "prompt=参考配图，使得动物们活跃起来，在场地里绕场一周的追逐" \
  -F "model=sora-2" \
  -F "size=1280x720" \
  -F "seconds=10" \
  -F "input_reference=@/path/to/image.png"
```

#### 成功响应 (200 OK)

```json
{
  "id": "video_abc123def456",
  "status": "submitted",
  "progress": 0,
  "prompt": "参考配图，使得动物们活跃起来，在场地里绕场一周的追逐",
  "model": "sora-2",
  "size": "1280x720",
  "seconds": "10",
  "created_at": 1704067200,
  "url": null,
  "completed_at": null
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 视频任务 ID，用于后续查询和下载 |
| `status` | string | 当前状态：`submitted`（已提交） |
| `progress` | integer | 生成进度：0-100 |
| `created_at` | integer | 创建时间戳（Unix 时间戳） |
| `url` | string | 视频 URL（完成后才有值） |
| `completed_at` | integer | 完成时间戳（完成后才有值） |

#### 错误响应

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Missing required parameter: prompt"
  }
}
```

---

### 2. 查询视频状态

#### 端点

```
GET /v1/videos/{video_id}
```

#### 请求头

```http
Authorization: sk-your-api-key-here
```

#### Curl 示例

```bash
curl -X GET "https://api.apiyi.com/v1/videos/video_abc123def456" \
  -H "Authorization: sk-your-api-key-here"
```

#### 成功响应 (200 OK)

**生成中**：

```json
{
  "id": "video_abc123def456",
  "status": "in_progress",
  "progress": 45,
  "prompt": "参考配图，使得动物们活跃起来，在场地里绕场一周的追逐",
  "model": "sora-2",
  "size": "1280x720",
  "seconds": "10",
  "created_at": 1704067200,
  "url": null,
  "completed_at": null
}
```

**生成完成**：

```json
{
  "id": "video_abc123def456",
  "status": "completed",
  "progress": 100,
  "prompt": "参考配图，使得动物们活跃起来，在场地里绕场一周的追逐",
  "model": "sora-2",
  "size": "1280x720",
  "seconds": "10",
  "created_at": 1704067200,
  "url": "https://api.apiyi.com/v1/videos/video_abc123def456/content",
  "completed_at": 1704067500
}
```

**生成失败**：

```json
{
  "id": "video_abc123def456",
  "status": "failed",
  "progress": 0,
  "error": "Content policy violation",
  "created_at": 1704067200
}
```

---

### 3. 下载视频内容

#### 端点

```
GET /v1/videos/{video_id}/content
```

#### 请求头

```http
Authorization: sk-your-api-key-here
```

#### Curl 示例

```bash
curl -X GET "https://api.apiyi.com/v1/videos/video_abc123def456/content" \
  -H "Authorization: sk-your-api-key-here" \
  -o video.mp4
```

#### 成功响应 (200 OK)

返回视频文件的二进制流（MP4 格式）

```http
Content-Type: video/mp4
Content-Length: 12345678
```

#### 注意事项

- 仅在 `status` 为 `completed` 时才能下载
- 视频文件格式：MP4（H.264 编码）
- 视频可能会在一段时间后过期，建议及时下载

---

## 状态说明

| 状态 | 说明 | 下一步操作 |
|------|------|-----------|
| `submitted` | 请求已提交，等待处理 | 继续轮询查询 |
| `in_progress` | 视频生成中 | 继续轮询查询 |
| `completed` | 视频生成完成 | 可以下载视频 |
| `failed` | 视频生成失败 | 检查错误信息，重新提交 |

### 状态转换流程

```
submitted → in_progress → completed
                ↓
              failed
```

---

## 错误处理

### 常见 HTTP 状态码

| 状态码 | 说明 | 解决方案 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查必填参数是否完整 |
| 401 | 认证失败 | 检查 API Key 是否正确 |
| 403 | 无权限 | 检查 API Key 是否有效或余额不足 |
| 404 | 资源不存在 | 检查 video_id 是否正确 |
| 429 | 请求过于频繁 | 增加轮询间隔 |
| 500 | 服务器错误 | 稍后重试 |

### 错误响应格式

```json
{
  "error": {
    "code": "error_code",
    "message": "详细错误信息",
    "type": "invalid_request_error"
  }
}
```

### 常见错误代码

| 错误代码 | 说明 | 解决方案 |
|---------|------|----------|
| `invalid_request` | 请求参数无效 | 检查参数格式和值 |
| `authentication_error` | 认证失败 | 检查 API Key |
| `rate_limit_exceeded` | 超过速率限制 | 降低请求频率 |
| `content_policy_violation` | 内容违规 | 修改 prompt 内容 |
| `insufficient_quota` | 配额不足 | 充值或升级套餐 |

---

## 最佳实践

### 1. Prompt 编写建议

**好的 Prompt 示例**：
```
一只可爱的金毛犬在公园草地上追逐飞盘，阳光明媚，背景是绿树和蓝天，
运动流畅，特写镜头跟随犬的动作，电影风格
```

**不好的 Prompt 示例**：
```
狗
```

**建议**：
- 详细描述场景、动作、风格
- 指定镜头类型（特写、远景、跟随等）
- 描述光线、色调、氛围
- 避免过于简短或模糊的描述
- 避免违规内容（暴力、色情等）

### 2. 图片参考建议

- **分辨率**：建议使用 1280x720 或更高分辨率
- **格式**：PNG 或 JPG
- **文件大小**：< 10MB
- **内容**：清晰、主体明确、光线良好
- **匹配**：图片内容应与 prompt 相关

### 3. 轮询策略

```python
# 推荐的轮询策略
POLL_INTERVAL = 30  # 30 秒查询一次
MAX_WAIT_TIME = 600  # 最长等待 10 分钟

# 不推荐：频繁查询会触发速率限制
POLL_INTERVAL = 5  # ❌ 太频繁
```

### 4. 错误重试策略

```python
import time

def retry_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i == max_retries - 1:
                raise
            wait_time = 2 ** i  # 指数退避：1s, 2s, 4s
            time.sleep(wait_time)
```

### 5. 资源管理

- **及时下载**：视频生成完成后尽快下载，避免过期
- **本地存储**：下载后立即保存到本地
- **清理缓存**：定期清理不需要的视频文件

---

## 示例代码

### Python

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
            'prompt': '视频描述',
            'model': 'sora-2',
            'size': '1280x720',
            'seconds': '10'
        }
        headers = {'Authorization': API_KEY}

        response = requests.post(BASE_URL, headers=headers, data=data, files=files)
        return response.json()['id']

# 第二步：轮询状态
def poll_status(video_id):
    headers = {'Authorization': API_KEY}

    while True:
        response = requests.get(f"{BASE_URL}/{video_id}", headers=headers)
        result = response.json()

        if result['status'] == 'completed':
            return True
        elif result['status'] == 'failed':
            return False

        time.sleep(30)

# 第三步：下载视频
def download_video(video_id):
    headers = {'Authorization': API_KEY}
    response = requests.get(f"{BASE_URL}/{video_id}/content", headers=headers)

    with open('video.mp4', 'wb') as f:
        f.write(response.content)

# 完整流程
video_id = submit_request()
if poll_status(video_id):
    download_video(video_id)
```

### JavaScript/Node.js

```javascript
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

const API_KEY = 'sk-your-api-key-here';
const BASE_URL = 'https://api.apiyi.com/v1/videos';

// 第一步：提交请求
async function submitRequest() {
    const formData = new FormData();
    formData.append('prompt', '视频描述');
    formData.append('model', 'sora-2');
    formData.append('size', '1280x720');
    formData.append('seconds', '10');
    formData.append('input_reference', fs.createReadStream('image.png'));

    const response = await axios.post(BASE_URL, formData, {
        headers: {
            ...formData.getHeaders(),
            'Authorization': API_KEY
        }
    });

    return response.data.id;
}

// 第二步：轮询状态
async function pollStatus(videoId) {
    while (true) {
        const response = await axios.get(`${BASE_URL}/${videoId}`, {
            headers: { 'Authorization': API_KEY }
        });

        if (response.data.status === 'completed') return true;
        if (response.data.status === 'failed') return false;

        await new Promise(resolve => setTimeout(resolve, 30000));
    }
}

// 第三步：下载视频
async function downloadVideo(videoId) {
    const response = await axios.get(`${BASE_URL}/${videoId}/content`, {
        headers: { 'Authorization': API_KEY },
        responseType: 'stream'
    });

    const writer = fs.createWriteStream('video.mp4');
    response.data.pipe(writer);

    return new Promise((resolve, reject) => {
        writer.on('finish', resolve);
        writer.on('error', reject);
    });
}

// 完整流程
(async () => {
    const videoId = await submitRequest();
    if (await pollStatus(videoId)) {
        await downloadVideo(videoId);
    }
})();
```

### Curl (Bash)

```bash
#!/bin/bash

API_KEY="sk-your-api-key-here"
BASE_URL="https://api.apiyi.com/v1/videos"

# 第一步：提交请求
response=$(curl -s -X POST "$BASE_URL" \
    -H "Authorization: $API_KEY" \
    -F "prompt=视频描述" \
    -F "model=sora-2" \
    -F "size=1280x720" \
    -F "seconds=10" \
    -F "input_reference=@image.png")

video_id=$(echo "$response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

# 第二步：轮询状态
while true; do
    response=$(curl -s -X GET "$BASE_URL/$video_id" \
        -H "Authorization: $API_KEY")

    status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

    if [ "$status" = "completed" ]; then
        break
    elif [ "$status" = "failed" ]; then
        exit 1
    fi

    sleep 30
done

# 第三步：下载视频
curl -X GET "$BASE_URL/$video_id/content" \
    -H "Authorization: $API_KEY" \
    -o video.mp4
```

---

## 配额和限制

| 限制项 | 值 | 说明 |
|--------|-----|------|
| 请求速率 | 10 次/分钟 | 超过会返回 429 错误 |
| 并发任务 | 5 个 | 同时处理的视频数量 |
| 视频时长 | 10 或 15 秒 | 不支持其他时长 |
| 图片大小 | < 10MB | 建议 < 5MB |
| Prompt 长度 | < 1000 字符 | 建议 100-300 字符 |

---

## 技术支持

如有问题，请联系：
- 技术支持邮箱：support@apiyi.com
- 文档更新：https://docs.apiyi.com

---

## 更新日志

### v1.0.0 (2025-10-29)
- 初始版本发布
- 支持 Sora-2 模型
- 支持异步视频生成
- 支持图片参考生成
