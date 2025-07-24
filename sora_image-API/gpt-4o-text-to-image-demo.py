#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文生图 API 调用示例 - 专门用于文本到图片的生成
"""

import requests
import json
import re
import time
from typing import Dict, Any, List

def generate_image_from_text(api_key: str, prompt: str, model: str = "gpt-4o-image", n: int = 1) -> Dict[str, Any]:
    """调用文生图 API 生成图片"""
    url = "https://vip.apiyi.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    if n > 1:
        payload["n"] = n
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return {}

def extract_image_urls(content: str) -> List[str]:
    """从响应内容中提取所有图片URL"""
    # 匹配 markdown 格式的图片链接
    pattern = r'!\[.*?\]\((https?://[^)]+)\)'
    urls = re.findall(pattern, content)
    
    # 如果没找到，尝试直接匹配URL
    if not urls:
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content)
    
    return urls

def download_image(url: str, image_type: str = "image") -> bool:
    """下载图片到本地，自动时间戳命名"""
    try:
        timestamp = int(time.time())
        ext = '.png' if '.' not in url.split('/')[-1] else '.' + url.split('/')[-1].split('.')[-1]
        filename = f"{image_type}_{timestamp}{ext}"
        
        print(f"正在下载: {filename}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ 下载成功: {filename}")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

def add_ratio(prompt: str, ratio: str = "2:3") -> str:
    """在提示词末尾添加尺寸比例"""
    if re.search(r'【\d+:\d+】$', prompt):
        return prompt
    if ratio not in ["2:3", "3:2", "1:1"]:
        ratio = "2:3"
    return f"{prompt}【{ratio}】"

def process_and_download(result: Dict[str, Any], image_type: str = "图片"):
    """处理API结果并自动下载图片"""
    if not result:
        print("API 调用失败!")
        return
    
    print("API 调用成功!")
    
    # 提取图片URL并下载
    if 'choices' in result and result['choices']:
        content = result['choices'][0].get('message', {}).get('content', '')
        urls = extract_image_urls(content)
        
        if urls:
            print(f"找到 {len(urls)} 张图片，开始下载...")
            for i, url in enumerate(urls, 1):
                download_image(url, f"{image_type}{i}" if len(urls) > 1 else image_type)
        else:
            print("未找到图片URL")

def demo_text_to_image():
    """文生图演示"""
    api_key = "sk-yWFV0EFZOrNUMGdtE6DbA02654214d1b8aA2028970B82b61"
    
    print("\n🎨 文生图演示")
    print("请选择测试类型:")
    print("1. 单张竖版图片 (2:3)")
    print("2. 多张横版图片 (3:2)")
    print("3. 方形图片 (1:1)")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == "1":
        print("\n生成单张猫咪图片 (2:3)")
        prompt = add_ratio("生成一只可爱的小猫", "2:3")
        result = generate_image_from_text(api_key, prompt)
        process_and_download(result, "猫咪")
    elif choice == "2":
        print("\n生成多张动漫人物合影图片 (3:2)")
        prompt = add_ratio("生成多张经典动漫人物的合影", "3:2")
        result = generate_image_from_text(api_key, prompt, n=2)
        process_and_download(result, "动漫人物")
    elif choice == "3":
        print("\n生成方形花朵图片 (1:1)")
        prompt = add_ratio("生成漂亮的玫瑰花", "1:1")
        result = generate_image_from_text(api_key, prompt)
        process_and_download(result, "花朵")
    else:
        print("无效选择!")



def main():
    """主函数 - 专门用于文生图"""
    print("🎨 文生图 API 演示")
    print("=" * 40)
    
    while True:
        demo_text_to_image()
        
        # 询问是否继续
        continue_choice = input("\n是否继续使用? (y/n): ").lower().strip()
        if continue_choice not in ['y', 'yes', '是', '1']:
            print("👋 再见!")
            break

if __name__ == "__main__":
    main() 