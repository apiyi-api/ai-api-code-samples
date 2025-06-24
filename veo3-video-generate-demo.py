#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APIYI Veo3 视频生成 API 快速示例
最简单的使用方式，5分钟上手
"""

import requests
import re

def generate_video(api_key, prompt):
    """
    生成视频的最简单方法
    
    Args:
        api_key: APIYI API密钥
        prompt: 视频生成提示词
    
    Returns:
        视频链接字典 {"watch_url": "...", "download_url": "..."}
    """
    
    # API配置
    url = "https://vip.apiyi.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 请求数据
    data = {
        "model": "veo3",
        "stream": False,
        "messages": [
            {
                "role": "system", 
                "content": "You are a video master, you can create a video script based on the user's request."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
    }
    
    # 发送请求
    try:
        response = requests.post(url, headers=headers, json=data, timeout=300)
        response.raise_for_status()
        
        # 获取响应内容
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 提取视频链接
        watch_match = re.search(r'\[▶️ Watch Online\]\(([^)]+)\)', content)
        download_match = re.search(r'\[⏬ Download Video\]\(([^)]+)\)', content)
        
        return {
            "success": True,
            "watch_url": watch_match.group(1) if watch_match else None,
            "download_url": download_match.group(1) if download_match else None,
            "raw_response": content
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# 快速使用示例
if __name__ == "__main__":
    # 替换为你的API易密钥，获取地址 https://www.apiyi.com/token
    API_KEY = "sk-"
    
    # 视频生成提示词
    prompt = "Inside a whimsical honeycomb-shaped room, a bee sits at a small table, deeply engrossed in a video game. The room and furniture are fashioned entirely out of beeswax, giving everything a warm, golden glow. The bee wears a tiny gaming headset, with honey jars and candles adding to the cozy, hive-like atmosphere. A pixelated game is displayed on a wax screen, while waxy gaming controls rest near the bee's tiny feet. The setting is playful and surreal, blending the textures of a natural hive with the vibrant personality of a high-tech gaming setup."
    
    print("🎬 开始生成视频...")
    print(f"📝 提示词: {prompt}")
    
    # 生成视频
    result = generate_video(API_KEY, prompt)
    
    if result["success"]:
        print("\n✅ 视频生成成功!")
        
        if result["watch_url"]:
            print(f"🎥 在线观看: {result['watch_url']}")
        
        if result["download_url"]:
            print(f"💾 下载链接: {result['download_url']}")
            
        print(f"\n📄 完整响应:")
        print(result["raw_response"])
        
    else:
        print(f"\n❌ 生成失败: {result['error']}") 
