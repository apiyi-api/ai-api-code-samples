from openai import OpenAI
import base64
import os
import requests
import time

# 使用中转站的 API
client = OpenAI(
  api_key="sk-", #API易的 KEY
  base_url="https://api.apiyi.com/v1"  # API易中转站的 base URL
)

prompt = """
A children's book drawing of a veterinarian using a stethoscope to 
listen to the heartbeat of a baby otter.
"""

try:
    print("正在调用 API 生成图片...")
    result = client.images.generate(
        model="flux-kontext-pro",
        prompt=prompt
    )
    
    print("API 响应:", result)
    
    if not result.data:
        print("错误：API 没有返回图片数据")
        exit(1)
    
    # 检查是否有 URL 或 base64 数据
    image_data = result.data[0]
    
    if image_data.url:
        # 如果返回的是 URL，下载图片
        print(f"正在从 URL 下载图片: {image_data.url}")
        response = requests.get(image_data.url)
        
        if response.status_code == 200:
            # 生成时间戳文件名
            timestamp = int(time.time())
            filename = f"otter_{timestamp}.png"
            
            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"图片已成功保存为 {filename}")
        else:
            print(f"下载图片失败，状态码: {response.status_code}")
            
    elif image_data.b64_json:
        # 如果返回的是 base64 数据
        print("正在处理 base64 图片数据...")
        image_base64 = image_data.b64_json
        image_bytes = base64.b64decode(image_base64)
        
        # 生成时间戳文件名
        timestamp = int(time.time())
        filename = f"otter_{timestamp}.png"
        
        with open(filename, "wb") as f:
            f.write(image_bytes)
        
        print(f"图片已成功保存为 {filename}")
    else:
        print("错误：API 既没有返回 URL 也没有返回 base64 数据")
        print("完整响应:", result)
        
except Exception as e:
    print(f"发生错误: {str(e)}")
    print(f"错误类型: {type(e)}")
    raise
