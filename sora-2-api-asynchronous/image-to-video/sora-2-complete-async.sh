#!/bin/bash

# Sora-2 视频生成完整异步流程 - Bash/Curl 版本
# 使用方法: bash sora-2-complete-async.sh

# ============================================
# 配置参数
# ============================================
API_KEY="sk-"
BASE_URL="https://api.apiyi.com/v1/videos"

PROMPT="参考配图，使得动物们活跃起来，在场地里绕场一周的追逐"
IMAGE_PATH="/Users/chenkang/Downloads/dog-and-cat.png"
MODEL="sora-2"
SIZE="1280x720"
SECONDS="10"

# 轮询配置
POLL_INTERVAL=30  # 每 30 秒查询一次
MAX_WAIT_TIME=600  # 最长等待 10 分钟

# ============================================
# 第一步：提交视频生成请求
# ============================================
step1_submit_request() {
    echo "============================================================"
    echo "第一步：提交视频生成请求"
    echo "============================================================"

    if [ ! -f "$IMAGE_PATH" ]; then
        echo "❌ 错误：图片文件不存在: $IMAGE_PATH"
        exit 1
    fi

    echo "📤 发送请求..."
    echo "   - 提示词: $PROMPT"
    echo "   - 图片: $IMAGE_PATH"
    echo "   - 尺寸: $SIZE"
    echo "   - 时长: ${SECONDS}秒"

    # 发送请求
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL" \
        -H "Authorization: $API_KEY" \
        -H "Accept: application/json" \
        -F "prompt=$PROMPT" \
        -F "model=$MODEL" \
        -F "size=$SIZE" \
        -F "seconds=$SECONDS" \
        -F "input_reference=@$IMAGE_PATH")

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

        echo "$video_id"
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
    local output_file="sora_video_${video_id##*_}.mp4"

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
    video_id=$(step1_submit_request)

    # 第二步：轮询状态
    step2_poll_status "$video_id"

    # 第三步：下载视频
    step3_download_video "$video_id"

    echo ""
    echo "============================================================"
    echo "🎉 完整流程执行成功!"
    echo "============================================================"
    echo "⏰ 结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
}

# 执行主流程
main
