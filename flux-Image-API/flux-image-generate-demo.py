"""
Flux 图像生成示例 - OpenAI 兼容格式调用

功能介绍：
使用 Flux Kontext Pro 模型通过文本提示词生成高质量图像

特点：
- 使用 OpenAI 兼容的调用方式，代码简洁易懂
- 支持自定义宽高比，从 3:7 (竖版) 到 7:3 (横版)
- 自动处理 URL 和 base64 两种返回格式
- 生成的图片自动保存到本地，文件名包含时间戳

使用前准备：
1. 安装依赖：pip install openai requests
2. 配置 API Key：将下方的 "sk-" 替换为您的真实 API Key
3. 根据需要修改提示词和宽高比参数

支持的参数：
- model: 模型名称，如 "flux-kontext-pro"
- prompt: 文本提示词，描述想要生成的图像
- aspect_ratio: 宽高比设置
  * "1:1" - 正方形 (1024x1024)
  * "2:3" - 竖版 (832x1248) 
  * "3:2" - 横版 (1248x832)
  * "16:9" - 宽屏横版 (1408x792)
  * "9:16" - 宽屏竖版 (792x1408)
  * "3:7" - 最窄竖版 (662x1544)
  * "7:3" - 最宽横版 (1544x662)

输出结果：
- 图片文件保存在当前目录
- 文件名格式：otter_{时间戳}.png
- 控制台显示生成过程和结果信息

使用示例：
python3 flux-kontext-pro-generate-demo.py

注意事项：
- 所有额外参数需要通过 extra_body 传递
- 支持同步调用，无需轮询等待
- 图片总像素约为 1MP，不同宽高比会调整具体尺寸
"""

from openai import OpenAI
import base64
import os
import requests
import time

# 中转站 API 配置
client = OpenAI(
  api_key="sk-", # 中转站 API KEY（按次计费）- 请替换为您的真实 API Key
  base_url="https://vip.apiyi.com/v1"  # 中转站的 base URL
)

# ===== 参数配置区域 =====
# 您可以根据需要修改以下参数

# 图像生成提示词 - 描述您想要生成的图像内容
prompt = """
A children's book drawing of a veterinarian using a stethoscope to 
listen to the heartbeat of a baby otter.
"""

# 图像宽高比设置 - 控制生成图像的长宽比例
aspect_ratio = "2:3"  # 当前设置为竖版 2:3
# 可选值：
# "1:1"  - 正方形
# "2:3"  - 竖版（适合手机壁纸）  
# "3:2"  - 横版（适合电脑壁纸）
# "16:9" - 宽屏（适合显示器）
# "9:16" - 竖屏（适合手机视频）
# "3:7"  - 超窄竖版
# "7:3"  - 超宽横版

try:
    print("🎨 正在调用 Flux API 生成图片...")
    print(f"📐 宽高比: {aspect_ratio}")
    print(f"💭 提示词: {prompt.strip()}")
    
    # OpenAI 兼容模式调用 - 通过 extra_body 传递 Flux 特有参数
    result = client.images.generate(
        model="flux-kontext-pro",              # 使用 Flux Kontext Pro 模型
        prompt=prompt,                         # 文本提示词
        extra_body={
            "aspect_ratio": aspect_ratio       # 自定义宽高比（必须通过 extra_body 传递）
        }
    )
    
    print("✅ API 调用成功！")
    print("📦 API 响应:", result)
    
    if not result.data:
        print("❌ 错误：API 没有返回图片数据")
        exit(1)
    
    # 处理返回的图片数据（支持 URL 和 base64 两种格式）
    image_data = result.data[0]
    
    if image_data.url:
        # 方式1：从 URL 下载图片（常见格式）
        print(f"🌐 正在从 URL 下载图片...")
        print(f"🔗 图片链接: {image_data.url}")
        response = requests.get(image_data.url)
        
        if response.status_code == 200:
            # 生成带时间戳的文件名，避免重复
            timestamp = int(time.time())
            filename = f"otter_{timestamp}.png"
            
            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"💾 图片已成功保存为: {filename}")
            print(f"📊 文件大小: {len(response.content)} 字节")
        else:
            print(f"❌ 下载图片失败，HTTP状态码: {response.status_code}")
            
    elif image_data.b64_json:
        # 方式2：处理 base64 编码的图片数据（备用格式）
        print("🔢 正在处理 base64 图片数据...")
        image_base64 = image_data.b64_json
        image_bytes = base64.b64decode(image_base64)
        
        # 生成带时间戳的文件名，避免重复
        timestamp = int(time.time())
        filename = f"otter_{timestamp}.png"
        
        with open(filename, "wb") as f:
            f.write(image_bytes)
        
        print(f"💾 图片已成功保存为: {filename}")
        print(f"📊 文件大小: {len(image_bytes)} 字节")
    else:
        print("❌ 错误：API 既没有返回 URL 也没有返回 base64 数据")
        print("🔍 完整响应内容:", result)
        
except Exception as e:
    print(f"💥 发生错误: {str(e)}")
    print(f"🔧 错误类型: {type(e)}")
    print("💡 请检查：")
    print("  - API Key 是否正确配置")
    print("  - 网络连接是否正常") 
    print("  - 中转站服务是否可用")
    raise

print("\n" + "="*50)
print("🎉 图片生成完成！")
print("📁 请查看当前目录中的新图片文件")
print("💡 提示：如需生成不同图片，请修改 prompt 或 aspect_ratio 参数")
print("="*50)