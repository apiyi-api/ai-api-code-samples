"""
Flux 图像编辑示例 - OpenAI 兼容格式调用

功能介绍：
图像编辑：基于原图和提示词编辑图像，可选择性使用蒙版指定编辑区域
支持本地文件和在线图片地址两种输入方式

使用前准备：
1. 安装依赖：pip install openai requests pillow
2. 配置 API Key：将下方的 "sk-" 替换为您的真实 API Key
3. 准备原图：确保当前目录有 "otter.png" 图片文件（或修改代码中的文件名/URL）

支持的参数：
- model: 模型名称，如 flux-kontext-max
- prompt: 编辑指令，描述想要如何修改图像
- aspect_ratio: 宽高比设置，支持从 3:7 (竖版) 到 7:3 (横版)
  * "1:1" - 正方形 (1024x1024)
  * "2:3" - 竖版 (832x1248) 
  * "3:2" - 横版 (1248x832)
  * "16:9" - 宽屏横版 (1408x792)
  * "9:16" - 宽屏竖版 (792x1408)
  * "3:7" - 最窄竖版 (662x1544)
  * "7:3" - 最宽横版 (1544x662)

注意事项：
- 图像编辑需要原图作为输入（支持本地文件或在线URL）
- 蒙版图片为可选，用于指定编辑区域（白色区域会被编辑）
- 支持的图片格式：PNG, JPEG, WEBP, 非动画GIF
- 单张图片大小限制：20MB
- 在线图片会自动下载到临时目录
- 生成的图片会保存在当前目录，文件名包含时间戳
- 所有额外参数需要通过 extra_body 传递（如 aspect_ratio）
- 支持同步调用，无需轮询等待
- 图片总像素约为 1MP，不同宽高比会调整具体尺寸

使用示例：
python3 flux-image-edit-demo.py
功能：编辑图像（修改背景、添加元素等）
"""

from openai import OpenAI
import base64
import os
import requests
import time
from PIL import Image
import tempfile
from io import BytesIO
from urllib.parse import urlparse

# 使用中转站的 API
client = OpenAI(
    api_key="sk-ntX75405TTgNPIi43e4aAd1094E54cB1B7D2A252E1Ad19B4",  # 中转站 API KEY（按次计费类型）- 请替换为您的真实 API Key
    base_url="https://vip.apiyi.com/v1"  # 中转站的 base URL
)

def download_image_from_url(url, save_dir=None):
    """从URL下载图片并返回本地文件路径"""
    try:
        print(f"正在从URL下载图片: {url}")
        
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 检查HTTP错误
        
        # 从URL获取文件扩展名
        parsed_url = urlparse(url)
        url_path = parsed_url.path
        
        # 尝试从URL路径获取扩展名
        if '.' in url_path:
            extension = url_path.split('.')[-1].lower()
            if extension not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                extension = 'jpg'  # 默认扩展名
        else:
            # 尝试从Content-Type获取格式
            content_type = response.headers.get('content-type', '').lower()
            if 'png' in content_type:
                extension = 'png'
            elif 'webp' in content_type:
                extension = 'webp'
            elif 'gif' in content_type:
                extension = 'gif'
            else:
                extension = 'jpg'
        
        # 创建临时文件名
        timestamp = int(time.time())
        if save_dir is None:
            save_dir = tempfile.gettempdir()
        
        filename = f"downloaded_image_{timestamp}.{extension}"
        file_path = os.path.join(save_dir, filename)
        
        # 保存图片
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"图片已下载到: {file_path}")
        
        # 验证图片是否有效
        try:
            with Image.open(file_path) as img:
                print(f"图片信息: {img.format}, 尺寸: {img.size}, 模式: {img.mode}")
        except Exception as e:
            print(f"警告：下载的文件可能不是有效图片: {e}")
        
        return file_path
        
    except Exception as e:
        print(f"下载图片失败: {e}")
        return None

def get_image_file(image_input):
    """
    处理图片输入，支持本地文件路径或在线URL
    返回本地文件路径
    """
    if not image_input:
        return None
        
    # 检查是否为URL
    if image_input.startswith(('http://', 'https://')):
        # 在线图片，需要先下载
        return download_image_from_url(image_input)
    else:
        # 本地文件路径
        if os.path.exists(image_input):
            return image_input
        else:
            print(f"错误：本地文件不存在 {image_input}")
            return None

def encode_image(image_path):
    """将图片编码为 base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def create_file(file_path):
    """上传文件到 OpenAI 并返回 file_id"""
    try:
        with open(file_path, "rb") as file:
            response = client.files.create(
                file=file,
                purpose="vision"
            )
        return response.id
    except Exception as e:
        print(f"文件上传失败: {e}")
        return None

def save_image_from_response(response_data, filename_prefix="edited_image"):
    """保存响应中的图片"""
    try:
        if hasattr(response_data, 'data') and response_data.data:
            image_data = response_data.data[0]
            
            if hasattr(image_data, 'url') and image_data.url:
                # 从 URL 下载图片
                print(f"正在从 URL 下载图片: {image_data.url}")
                response = requests.get(image_data.url)
                if response.status_code == 200:
                    timestamp = int(time.time())
                    filename = f"{filename_prefix}_{timestamp}.png"
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    print(f"图片已保存为: {filename}")
                    return filename
                    
            elif hasattr(image_data, 'b64_json') and image_data.b64_json:
                # 处理 base64 数据
                print("正在处理 base64 图片数据...")
                image_bytes = base64.b64decode(image_data.b64_json)
                timestamp = int(time.time())
                filename = f"{filename_prefix}_{timestamp}.png"
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                print(f"图片已保存为: {filename}")
                return filename
                
        print("错误：无法从响应中提取图片数据")
        return None
    except Exception as e:
        print(f"保存图片时发生错误: {e}")
        return None

def cleanup_temp_files(file_paths):
    """清理临时文件"""
    for file_path in file_paths:
        if file_path and file_path.startswith(tempfile.gettempdir()):
            try:
                os.remove(file_path)
                print(f"已清理临时文件: {file_path}")
            except Exception as e:
                print(f"清理临时文件失败: {e}")

# 图像编辑功能
def edit_image_example():
    """
    图像编辑示例 - 基于原图和提示词编辑图像
    支持本地文件和在线URL两种输入方式
    
    功能：根据提示词对现有图像进行编辑，如修改背景、添加或删除元素等
    输入：原始图片（本地文件或URL）+ 编辑提示词 + 可选蒙版图片
    输出：编辑后的图片
    
    蒙版使用说明：
    - 蒙版图片中的白色区域会被编辑
    - 黑色区域会被保留不变
    - 如果不提供蒙版，AI 会自动决定编辑区域
    """
    
    # 配置参数 - 支持本地文件或在线URL
    # 示例1：本地文件
    original_image = "otter.png"  # 原始图片文件名
    
    # 示例2：在线图片URL（取消注释下面一行来使用在线图片）
    # original_image = "https://example.com/path/to/your/image.jpg"
    
    mask_image = None  # 蒙版图片文件名（可选，如 "mask.png" 或在线URL）
    
    # 图像宽高比设置 - 控制编辑后图像的长宽比例
    aspect_ratio = "1:1"  # 默认为正方形
    # 可选值：
    # "1:1"  - 正方形
    # "2:3"  - 竖版（适合手机壁纸）  
    # "3:2"  - 横版（适合电脑壁纸）
    # "16:9" - 宽屏（适合显示器）
    # "9:16" - 竖屏（适合手机视频）
    # "3:7"  - 超窄竖版
    # "7:3"  - 超宽横版
    
    # 临时文件列表，用于最后清理
    temp_files = []
    
    try:
        # 处理原始图片（本地文件或在线下载）
        original_file_path = get_image_file(original_image)
        if not original_file_path:
            print(f"错误：无法获取原始图片 {original_image}")
            print("请确保文件存在或URL可访问")
            return
        
        # 如果是从URL下载的，添加到临时文件列表
        if original_image.startswith(('http://', 'https://')):
            temp_files.append(original_file_path)
        
        # 处理蒙版图片（如果指定）
        mask_file_path = None
        if mask_image:
            mask_file_path = get_image_file(mask_image)
            if not mask_file_path:
                print(f"警告：无法获取蒙版图片 {mask_image}，将继续无蒙版编辑")
            elif mask_image.startswith(('http://', 'https://')):
                temp_files.append(mask_file_path)
        
        # 编辑提示词 - 描述您希望如何修改图片
        prompt = "Only remove the two adults in the picture, and keep the others unchanged"
        
        print("正在编辑图片...")
        print(f"📐 宽高比: {aspect_ratio}")
        print(f"💭 编辑提示: {prompt}")
        
        # 准备 API 调用参数 - 使用 OpenAI 兼容格式，通过 extra_body 传递 Flux 特有参数
        edit_params = {
            "model": "flux-kontext-max",           # 使用的模型
            "image": open(original_file_path, "rb"),   # 原始图片文件
            "prompt": prompt,                      # 编辑指令
            "extra_body": {
                "aspect_ratio": aspect_ratio       # 自定义宽高比（必须通过 extra_body 传递）
            }
        }
        
        # 如果指定了蒙版图片，添加到参数中
        if mask_file_path:
            edit_params["mask"] = open(mask_file_path, "rb")
            print(f"使用蒙版图片: {mask_image}")
        else:
            print("未使用蒙版，AI 将自动决定编辑区域")
        
        result = client.images.edit(**edit_params)
        
        # 添加调试信息
        print("API 响应类型:", type(result))
        print("API 响应内容:", result)
        
        # 保存结果
        filename = save_image_from_response(result, "edited")
        if filename:
            print(f"图片编辑完成！保存为: {filename}")
            print(f"原始图片: {original_image}")
            print(f"编辑提示: {prompt}")
            print(f"宽高比: {aspect_ratio}")
        
    except Exception as e:
        print(f"图片编辑失败: {e}")
        print(f"错误类型: {type(e)}")
    
    finally:
        # 清理临时文件
        cleanup_temp_files(temp_files)

if __name__ == "__main__":
    print("=== Flux 图像编辑示例 - OpenAI 兼容格式 (支持在线图片) ===")
    print("\n🖼️ 功能介绍:")
    print("图像编辑 - 使用 Flux Kontext Max 模型根据提示词修改现有图片")
    print("支持本地文件和在线图片URL两种输入方式，可自定义宽高比")
    print("\n📋 使用前请确保:")
    print("- 当前目录有 'otter.png' 图片文件，或在代码中配置在线图片URL")
    print("- 已配置正确的 API Key") 
    print("- 安装了必要依赖: pip install openai requests pillow")
    print("- 可在代码中修改 aspect_ratio 参数来调整输出图片比例")
    
    print("\n🎨 开始图像编辑...")
    edit_image_example() 