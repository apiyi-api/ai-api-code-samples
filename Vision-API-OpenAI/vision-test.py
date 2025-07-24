import requests
import json
import base64
import time
from PIL import Image
from io import BytesIO
import os

def load_image_to_base64(image_path):
    """将本地图片转换为base64编码"""
    try:
        with open(image_path, "rb") as image_file:
            # 读取图片数据
            image_data = image_file.read()
            # 转换为base64
            base64_encoded = base64.b64encode(image_data).decode('utf-8')
            return base64_encoded
    except Exception as e:
        print(f"图片加载失败: {e}")
        return None

def api_inference(prompt, base64_image, model_id="gemini-2.5-pro", api_key="sk-"):
    """调用API进行图像视觉理解"""
    url = "https://vip.apiyi.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
        }}
    ]
    payload = {"model": model_id, "messages": [{"role": "user", "content": content}]}
    
    try:
        print("🤖 正在调用Gemini 2.5 Pro进行图像视觉理解...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # 提取AI的回复
        if "choices" in result and result["choices"]:
            ai_response = result["choices"][0]["message"]["content"]
            return ai_response
        else:
            print("❌ API响应格式异常")
            return None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def save_analysis_result(result, image_path):
    """保存分析结果到文件"""
    timestamp = int(time.time())
    result_file = f"analysis_result_{timestamp}.txt"
    
    try:
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(f"图片路径: {image_path}\n")
            f.write(f"分析时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}\n")
            f.write(f"模型: Gemini 2.5 Pro\n")
            f.write("-" * 50 + "\n")
            f.write("AI视觉理解结果:\n")
            f.write(result)
        
        print(f"📄 分析结果已保存到: {result_file}")
        return result_file
    except Exception as e:
        print(f"❌ 保存结果失败: {e}")
        return None

def main():
    """主函数"""
    print("🔍 Gemini 2.5 Pro 图片视觉理解系统")
    print("=" * 50)
    
    # 检查图片是否存在
    image_path = "otter.png"
    if not os.path.exists(image_path):
        print(f"❌ 找不到图片文件: {image_path}")
        print("请确保在当前目录下有 otter.png 文件")
        return
    
    print(f"📸 发现图片: {image_path}")
    
    # 加载图片并转换为base64
    base64_image = load_image_to_base64(image_path)
    if not base64_image:
        print("❌ 图片加载失败")
        return
    
    print("✅ 图片已成功转换为base64格式")
    
    # 定义分析提示词
    prompt = """
    请详细分析这张图片，包括：
    1. 图片中的主要对象或动物
    2. 对象的外观特征、颜色、姿态
    3. 背景环境描述
    4. 图片的整体风格和色调
    5. 图片给人的情感感受
    
    请用中文详细描述你看到的内容。
    """
    
    # 调用API进行视觉理解
    result = api_inference(prompt, base64_image)
    
    if result:
        print("\n🎯 AI视觉理解结果:")
        print("-" * 30)
        print(result)
        print("-" * 30)
        
        # 保存结果
        save_analysis_result(result, image_path)
        print("\n✅ 图片视觉理解完成!")
    else:
        print("❌ 视觉理解失败，请检查API配置或网络连接")

if __name__ == "__main__":
    main()