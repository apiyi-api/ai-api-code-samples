#!/bin/bash

# Sora-2 视频生成完整异步流程 - Bash/Curl 版本
# 智能双模式：自动识别文字生成视频 / 图片生成视频
# 使用方法: bash sora-2-async.sh

# ============================================
# 配置参数
# ============================================
API_KEY="sk-"
BASE_URL="https://api.apiyi.com/v1/videos"

# ==================== 模式配置 ====================
# 设置 IMAGE_PATH 来切换生成模式：
# - IMAGE_PATH="" (留空)        → 文字生成视频
# - IMAGE_PATH="/path/to/image" → 图片生成视频
# =================================================

IMAGE_PATH=""  # 文字生成视频模式
# IMAGE_PATH="/path/to/your/image.png"  # 取消注释并设置路径，切换为图片生成视频模式

PROMPT="一只橘色的小猫在阳光明媚的花园里追逐蝴蝶"
MODEL="sora-2"
SIZE="1280x720"
SECONDS="15"

# 轮询配置
POLL_INTERVAL=30  # 每 30 秒查询一次
MAX_WAIT_TIME=600  # 最长等待 10 分钟

# ============================================
# 第一步：提交视频生成请求（自动识别文字或图片模式）
# ============================================
step1_submit_request() {
    echo "============================================================"
    echo "第一步：提交视频生成请求"
    echo "============================================================"

    # 检查是否为图片生成模式
    local is_image_mode=false
    if [ -n "$IMAGE_PATH" ] && [ -f "$IMAGE_PATH" ]; then
        is_image_mode=true
    fi

    if [ -n "$IMAGE_PATH" ] && [ ! -f "$IMAGE_PATH" ]; then
        echo "⚠️  警告：图片路径已设置但文件不存在: $IMAGE_PATH"
        echo "    将使用文字生成视频模式"
    fi

    # 发送请求
    if [ "$is_image_mode" = true ]; then
        # 图片生成视频模式
        echo "📷 模式：图片生成视频"
        echo "📤 发送请求..."
        echo "   - 提示词: $PROMPT"
        echo "   - 图片: $IMAGE_PATH"
        echo "   - 模型: $MODEL"
        echo "   - 尺寸: $SIZE"
        echo "   - 时长: ${SECONDS}秒"

        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL" \
            -H "Authorization: $API_KEY" \
            -H "Accept: application/json" \
            -F "prompt=$PROMPT" \
            -F "model=$MODEL" \
            -F "size=$SIZE" \
            -F "seconds=$SECONDS" \
            -F "input_reference=@$IMAGE_PATH")
    else
        # 文字生成视频模式
        echo "📝 模式：文字生成视频"
        echo "📤 发送请求..."
        echo "   - 提示词: $PROMPT"
        echo "   - 模型: $MODEL"
        echo "   - 尺寸: $SIZE"
        echo "   - 时长: ${SECONDS}秒"

        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL" \
            -H "Authorization: $API_KEY" \
            -H "Accept: application/json" \
            -F "prompt=$PROMPT" \
            -F "model=$MODEL" \
            -F "size=$SIZE" \
            -F "seconds=$SECONDS")
    fi

    # 分离响应体和状态码
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ]; then
        # 提取 video_id
        video_id=$(echo "$response_body" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
        status=$(echo "$response_body" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)

        echo "✅ 请求提交成功!"
        echo "   - 视频ID: $video_id"
        echo "   - 状态: $status"
        echo "   ⏱️  预计生成时间: 3-5 分钟"

        # 返回 video_id 和 is_image_mode
        echo "$video_id|$is_image_mode"
        return 0
    else
        echo "❌ 请求失败: HTTP $http_code"
        echo "   响应: $response_body"
        exit 1
    fi
}

# ============================================
# 第二步：轮询查询视频状态
# ============================================
step2_poll_status() {
    local video_id=$1

    echo ""
    echo "============================================================"
    echo "第二步：查询视频生成状态"
    echo "============================================================"
    echo "💡 提示：视频生成通常需要 3-5 分钟，每 ${POLL_INTERVAL} 秒自动查询一次"

    local start_time=$(date +%s)

    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        # 检查超时
        if [ $elapsed -gt $MAX_WAIT_TIME ]; then
            echo "⏱️ 超时：已等待 $MAX_WAIT_TIME 秒，停止查询"
            exit 1
        fi

        echo ""
        echo "🔍 查询状态... (已等待 ${elapsed} 秒)"

        # 查询状态
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/$video_id" \
            -H "Authorization: $API_KEY")

        http_code=$(echo "$response" | tail -n1)
        response_body=$(echo "$response" | sed '$d')

        if [ "$http_code" -eq 200 ]; then
            status=$(echo "$response_body" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
            progress=$(echo "$response_body" | grep -o '"progress":[0-9]*' | head -1 | cut -d':' -f2)

            echo "   - 状态: $status"
            echo "   - 进度: ${progress:-0}%"

            if [ "$status" = "completed" ]; then
                echo "✅ 视频生成完成!"
                return 0
            elif [ "$status" = "failed" ]; then
                echo "❌ 视频生成失败"
                exit 1
            else
                echo "⏳ 视频生成中，等待 ${POLL_INTERVAL} 秒后继续查询..."
                sleep $POLL_INTERVAL
            fi
        else
            echo "❌ 状态查询失败: HTTP $http_code"
            sleep $POLL_INTERVAL
        fi
    done
}

# ============================================
# 第三步：下载视频
# ============================================
step3_download_video() {
    local video_id=$1
    local is_image_mode=$2

    # 根据模式生成文件名
    local mode_prefix="text"
    if [ "$is_image_mode" = "true" ]; then
        mode_prefix="image"
    fi
    local output_file="sora_${mode_prefix}_video_${video_id##*_}.mp4"

    echo ""
    echo "============================================================"
    echo "第三步：下载视频"
    echo "============================================================"

    echo "📥 开始下载视频..."

    # 下载视频
    http_code=$(curl -w "%{http_code}" -o "$output_file" -X GET "$BASE_URL/$video_id/content" \
        -H "Authorization: $API_KEY")

    if [ "$http_code" -eq 200 ]; then
        file_size=$(ls -lh "$output_file" | awk '{print $5}')
        echo "✅ 视频下载成功!"
        echo "   - 保存路径: $(pwd)/$output_file"
        echo "   - 文件大小: $file_size"
        return 0
    else
        echo "❌ 下载失败: HTTP $http_code"
        exit 1
    fi
}

# ============================================
# 主流程
# ============================================
main() {
    echo ""
    echo "🎬 开始 Sora-2 视频生成完整流程"
    echo "⏰ 开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # 第一步：提交请求
    result=$(step1_submit_request)
    video_id=$(echo "$result" | cut -d'|' -f1)
    is_image_mode=$(echo "$result" | cut -d'|' -f2)

    # 第二步：轮询状态
    step2_poll_status "$video_id"

    # 第三步：下载视频
    step3_download_video "$video_id" "$is_image_mode"

    echo ""
    echo "============================================================"
    echo "🎉 完整流程执行成功!"
    echo "============================================================"
    echo "⏰ 结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
}

# 执行主流程
main
