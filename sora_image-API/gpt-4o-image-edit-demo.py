#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图生图 API 调用示例 - 专门用于图片到图片的转换
"""

import requests
import json
import re
import time
from typing import Dict, Any, List

def generate_image_from_image(api_key: str, prompt: str, image_urls: List[str], model: str = "gpt-4o-image") -> Dict[str, Any]:
    """调用图生图 API 生成图片"""
    url = "https://vip.apiyi.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # 构建content - 图生图使用数组格式
    content = [{"type": "text", "text": prompt}]
    for img_url in image_urls:
        content.append({
            "type": "image_url",
            "image_url": {"url": img_url}
        })
    
    payload = {"model": model, "messages": [{"role": "user", "content": content}]}
    
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

def demo_image_to_image():
    """图生图演示"""
    api_key = "sk-"
    
    print("\n🖼️ 图生图演示")
    print("请选择输入方式:")
    print("1. 使用预设示例URL (推荐)")
    print("2. 手动输入图片URL")
    
    input_choice = input("请输入选择 (1-2): ").strip()
    
    if input_choice == "1":
        # 预设的示例URL
        preset_examples = {
            "1": {
                "name": "单张猫咪图片",
                "urls": ["https://tokensceshi.oss-ap-southeast-1.aliyuncs.com/sora/51f9748a-fd6c-483c-be7d-50ac56d64584.png"],
                "prompts": ["改成3只猫猫", "添加彩虹背景", "变成卡通风格"]
            },
            "2": {
                "name": "多张图片处理（比如融合、组合）",
                "urls": [
                    "https://tokensceshi.oss-ap-southeast-1.aliyuncs.com/sora/51f9748a-fd6c-483c-be7d-50ac56d64584.png",
                    "https://tokensceshi.oss-ap-southeast-1.aliyuncs.com/sora/51f9748a-fd6c-483c-be7d-50ac56d64584.png"
                ],
                "prompts": ["两张图片融合到一个场景", "改成黑白风格"]
            }
        }
        
        print("\n选择预设示例:")
        for key, example in preset_examples.items():
            print(f"{key}. {example['name']} ({len(example['urls'])}张图片)")
        
        example_choice = input("请输入选择 (1-2): ").strip()
        
        if example_choice in preset_examples:
            selected = preset_examples[example_choice]
            image_urls = selected["urls"]
            
            print(f"\n已选择: {selected['name']}")
            print(f"图片数量: {len(image_urls)}张")
            print("图片URL:")
            for i, url in enumerate(image_urls, 1):
                print(f"  {i}. {url}")
            
            print(f"\n推荐修改描述:")
            for i, prompt_suggestion in enumerate(selected["prompts"], 1):
                print(f"  {i}. {prompt_suggestion}")
            
            prompt = input(f"\n请输入修改描述 (直接回车使用第1个推荐): ").strip()
            if not prompt:
                prompt = selected["prompts"][0]
            
            print(f"\n正在处理 {len(image_urls)} 张图片...")
            print(f"修改描述: {prompt}")
            result = generate_image_from_image(api_key, prompt, image_urls)
            process_and_download(result, "修改后")
        else:
            print("无效选择!")
            
    elif input_choice == "2":
        # 手动输入功能
        print("\n请输入要修改的图片URL (多个URL用空格分隔):")
        urls_input = input("图片URL: ").strip()
        if not urls_input:
            print("未输入图片URL!")
            return
        
        image_urls = urls_input.split()
        print(f"将处理 {len(image_urls)} 张图片")
        
        prompt = input("请输入修改描述: ").strip()
        if not prompt:
            prompt = "改成更美观的风格"
        
        print(f"\n正在处理图片...")
        result = generate_image_from_image(api_key, prompt, image_urls)
        process_and_download(result, "修改后")
    else:
        print("无效选择!")

def main():
    """主函数 - 专门用于图生图"""
    print("🖼️ 图生图 API 专用演示")
    print("=" * 40)
    
    while True:
        demo_image_to_image()
        
        # 询问是否继续
        continue_choice = input("\n是否继续使用? (y/n): ").lower().strip()
        if continue_choice not in ['y', 'yes', '是', '1']:
            print("👋 再见!")
            break

if __name__ == "__main__":
    main() 