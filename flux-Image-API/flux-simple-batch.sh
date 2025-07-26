#!/bin/bash

# 确保使用bash执行
if [ -z "$BASH_VERSION" ]; then
    echo "错误: 此脚本需要bash环境，请使用: bash $0"
    exit 1
fi

# FLUX 图像合成批量处理 - 双图片版本
# 将两张图片合并后进行AI处理，实现图案转移效果

set -e

# 配置变量
API_KEY="sk-"
API_URL="https://vip.apiyi.com/v1/images/edits"
MODEL="flux-kontext-max"
SIZE="1024x1024"
OUTPUT_DIR="./batch_output"
TEMP_DIR="./temp_images"

# 【修改这里】统一提示词 - 描述如何处理合并后的图片
BATCH_PROMPT="Look at the left image and right image. Transfer the pattern/design from the left image to the clothes of the model in the right image, with the size being 2/3 of the width of the chest, located in the middle. Make it look natural and well-integrated."

# 【修改这里】图片对数组 - 每对包含参考图和基础图
# 格式：每行一对，用"|"分隔 "参考图URL|基础图URL"
IMAGE_PAIRS=(
    "http://8.153.165.164:9000/ycm/aeaf84d7-10ba-4b2c-91f7-245d25582bb3.jpeg|http://8.153.165.164:9000/ycm/e70d685f-5380-4892-8b49-7423b20fe500.png"
    # 添加更多图片对...
    # "参考图URL|基础图URL"
)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 创建必要的目录
create_directories() {
    log_info "创建工作目录..."
    mkdir -p "$OUTPUT_DIR" "$TEMP_DIR"
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    rm -rf "$TEMP_DIR"
}

# 下载图片
download_image() {
    local url=$1
    local output_file=$2
    local description=$3
    
    log_info "正在下载${description}: $url"
    
    if curl -L -s -o "$output_file" "$url"; then
        if [ -f "$output_file" ] && [ -s "$output_file" ]; then
            log_success "${description}下载成功: $(basename "$output_file")"
            return 0
        else
            log_error "下载的文件为空或不存在"
            return 1
        fi
    else
        log_error "${description}下载失败"
        return 1
    fi
}

# 合并两张图片（左右排列）
merge_images() {
    local reference_image=$1
    local base_image=$2
    local output_image=$3
    
    log_info "正在合并图片..."
    
    # 检查是否安装了ImageMagick
    if ! command -v convert &> /dev/null; then
        log_error "未安装ImageMagick，尝试使用Python PIL进行图片合并"
        
        # 使用Python进行图片合并
        python3 -c "
import sys
from PIL import Image
import os

try:
    # 打开两张图片
    img1 = Image.open('$reference_image')
    img2 = Image.open('$base_image')
    
    # 统一高度到较小的那个
    height = min(img1.height, img2.height)
    
    # 按比例调整宽度
    width1 = int(img1.width * height / img1.height)
    width2 = int(img2.width * height / img2.height)
    
    # 调整图片大小
    img1_resized = img1.resize((width1, height), Image.LANCZOS)
    img2_resized = img2.resize((width2, height), Image.LANCZOS)
    
    # 创建合并后的图片
    total_width = width1 + width2
    merged_img = Image.new('RGB', (total_width, height))
    
    # 粘贴图片
    merged_img.paste(img1_resized, (0, 0))
    merged_img.paste(img2_resized, (width1, 0))
    
    # 保存合并后的图片
    merged_img.save('$output_image')
    print('SUCCESS')
    
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"
        
        if [ $? -eq 0 ]; then
            log_success "图片合并成功: $(basename "$output_image")"
            return 0
        else
            log_error "Python图片合并失败"
            return 1
        fi
    else
        # 使用ImageMagick进行图片合并
        if convert "$reference_image" "$base_image" +append "$output_image"; then
            log_success "图片合并成功: $(basename "$output_image")"
            return 0
        else
            log_error "ImageMagick图片合并失败"
            return 1
        fi
    fi
}

# 处理图片对
process_image_pair() {
    local pair_data=$1
    local prompt=$2
    local index=$3
    
    # 分离参考图和基础图URL
    local reference_url=$(echo "$pair_data" | cut -d'|' -f1)
    local base_url=$(echo "$pair_data" | cut -d'|' -f2)
    
    log_info "=== 处理第 $index 对图片 ==="
    log_info "参考图URL: $reference_url"
    log_info "基础图URL: $base_url"
    log_info "提示词: $prompt"
    
    # 生成临时文件名
    local temp_reference="$TEMP_DIR/reference_${index}.jpg"
    local temp_base="$TEMP_DIR/base_${index}.jpg"
    local temp_merged="$TEMP_DIR/merged_${index}.jpg"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local output_file="$OUTPUT_DIR/pattern_transfer_${index}_${timestamp}.png"
    
    # 下载参考图
    if ! download_image "$reference_url" "$temp_reference" "参考图"; then
        log_error "跳过第 $index 对图片（参考图下载失败）"
        return 1
    fi
    
    # 下载基础图
    if ! download_image "$base_url" "$temp_base" "基础图"; then
        log_error "跳过第 $index 对图片（基础图下载失败）"
        return 1
    fi
    
    # 合并两张图片
    if ! merge_images "$temp_reference" "$temp_base" "$temp_merged"; then
        log_error "跳过第 $index 对图片（图片合并失败）"
        return 1
    fi
    
    # 调用API - 使用合并后的图片
    log_info "正在调用 FLUX API进行图像处理..."
    
    # 保存响应到临时文件
    temp_response=$(mktemp)
    curl -s -o "$temp_response" -w "%{http_code}" "$API_URL" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: multipart/form-data" \
        -F "model=$MODEL" \
        -F "image=@$temp_merged" \
        -F "prompt=$prompt" \
        -F "n=1" \
        -F "size=$SIZE" > /tmp/http_code_${index}.txt
    
    http_code=$(cat /tmp/http_code_${index}.txt)
    response_body=$(cat "$temp_response")
    
    log_info "HTTP状态码: $http_code"
    
    if [ "$http_code" -eq 200 ]; then
        log_success "API调用成功"
        
        # 解析JSON并获取图片URL
        result_url=$(echo "$response_body" | jq -r '.data[0].url' 2>/dev/null)
        
        if [ "$result_url" != "null" ] && [ "$result_url" != "" ]; then
            log_info "正在下载处理结果..."
            
            if curl -L -s -o "$output_file" "$result_url"; then
                log_success "第 $index 对图片处理完成: $output_file"
                
                # 显示文件信息
                if [ -f "$output_file" ]; then
                    file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
                    log_info "文件大小: $(($file_size/1024))KB"
                fi
                
                # 保存合并后的原图作为参考
                cp "$temp_merged" "$OUTPUT_DIR/merged_reference_${index}_${timestamp}.jpg"
                log_info "合并后的原图保存为: merged_reference_${index}_${timestamp}.jpg"
                
            else
                log_error "第 $index 对图片处理结果下载失败"
                return 1
            fi
        else
            log_error "无法从响应中获取图片URL"
            return 1
        fi
    else
        log_error "API调用失败，状态码: $http_code"
        log_info "响应内容:"
        echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
        return 1
    fi
    
    # 清理临时文件
    rm -f "$temp_response" "/tmp/http_code_${index}.txt"
}

# 批量处理图片对
batch_process() {
    log_info "=== FLUX 图像合成批量处理开始 ==="
    log_info "使用提示词: $BATCH_PROMPT"
    log_info "处理图片对数量: ${#IMAGE_PAIRS[@]}"
    
    local total_count=0
    local success_count=0
    local failed_count=0
    
    for pair_data in "${IMAGE_PAIRS[@]}"; do
        ((total_count++))
        
        if process_image_pair "$pair_data" "$BATCH_PROMPT" "$total_count"; then
            ((success_count++))
        else
            ((failed_count++))
        fi
        
        echo ""
    done
    
    # 显示统计信息
    log_info "=== 批量处理完成 ==="
    log_info "总计: $total_count 对图片"
    log_success "成功: $success_count 对图片"
    if [ $failed_count -gt 0 ]; then
        log_error "失败: $failed_count 对图片"
    fi
    
    if [ $success_count -gt 0 ]; then
        log_success "处理结果保存在: $OUTPUT_DIR"
    fi
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查jq
    if ! command -v jq &> /dev/null; then
        log_error "此脚本需要jq来解析JSON响应"
        log_info "请安装jq: brew install jq"
        return 1
    fi
    
    # 检查Python和PIL
    if ! command -v python3 &> /dev/null; then
        log_error "未安装Python3"
        return 1
    fi
    
    if ! python3 -c "import PIL" 2>/dev/null; then
        log_warning "未安装PIL，正在尝试安装..."
        if ! pip3 install Pillow; then
            log_error "PIL安装失败，图片合并功能不可用"
            return 1
        fi
    fi
    
    log_success "所有依赖检查通过"
    return 0
}

# 主函数
main() {
    log_info "=== FLUX 图像合成批量处理工具 (双图片版本) ==="
    
    # 检查依赖
    if ! check_dependencies; then
        exit 1
    fi
    
    # 检查是否有图片对
    if [ ${#IMAGE_PAIRS[@]} -eq 0 ]; then
        log_error "没有找到要处理的图片对"
        log_info "请编辑脚本中的 IMAGE_PAIRS 数组添加图片对"
        exit 1
    fi
    
    create_directories
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    # 开始处理
    batch_process
}

# 使用说明
show_usage() {
    echo "FLUX 图像合成批量处理工具 - 双图片版本"
    echo ""
    echo "功能: 将参考图的元素/图案转移到基础图的衣服上"
    echo "原理: 先将两张图片合并，然后使用AI进行图案转移"
    echo ""
    echo "使用方法:"
    echo "  $0          # 开始批量处理"
    echo "  $0 --help   # 显示帮助"
    echo ""
    echo "依赖要求:"
    echo "  - jq (JSON处理): brew install jq"
    echo "  - Python3 + PIL: pip3 install Pillow"
    echo "  - ImageMagick (可选): brew install imagemagick"
    echo ""
    echo "配置说明:"
    echo "  1. 修改 BATCH_PROMPT 变量设置提示词"
    echo "  2. 修改 IMAGE_PAIRS 数组添加图片对"
    echo "  3. 运行脚本开始处理"
    echo ""
    echo "示例:"
    echo "  BATCH_PROMPT=\"Transfer the pattern from left image to the clothes in right image\""
    echo "  IMAGE_PAIRS=("
    echo "    \"http://example.com/pattern.jpg|http://example.com/model.jpg\""
    echo "    \"http://example.com/design.jpg|http://example.com/shirt.jpg\""
    echo "  )"
    echo ""
    echo "格式说明:"
    echo "  - 每对图片用 '|' 分隔"
    echo "  - 左边是参考图(提供元素/图案)"
    echo "  - 右边是基础图(目标衣服)"
    echo "  - 脚本会自动下载、合并图片，然后调用AI处理"
}

# 检查参数
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
fi

# 运行主函数
main "$@" 