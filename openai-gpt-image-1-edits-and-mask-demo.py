import requests
import json
import os
import base64
import argparse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 解析命令行参数
def parse_arguments():
    parser = argparse.ArgumentParser(description='OpenAI 图像编辑 API 测试工具')
    parser.add_argument('--image', type=str, default="input_image.png", help='输入图像文件路径')
    parser.add_argument('--mask', type=str, default="mask_image.png", help='遮罩图像文件路径')
    parser.add_argument('--prompt', type=str, default="将图像中的背景替换为蓝色，保持主体不变", 
                        help='编辑提示词')
    parser.add_argument('--size', type=str, default="1024x1024", 
                        choices=["1024x1024", "1536x1024", "1024x1536"], 
                        help='输出图像尺寸')
    return parser.parse_args()

# 设置API密钥和URL
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("未找到 OPENAI_API_KEY 环境变量，请在 .env 文件中设置")

url = "https://vip.apiyi.com/v1/images/edits"

# 设置请求头
headers = {
    "Authorization": f"Bearer {api_key}"
}

# 获取命令行参数
args = parse_arguments()
image_path = args.image
mask_path = args.mask
prompt = args.prompt
size = args.size

# 准备请求数据
data = {
    'model': 'gpt-image-1',
    'prompt': prompt,
    'n': '1',
    'size': size,
    'response_format': 'b64_json'
}

print(f"正在调用API进行图像编辑: {prompt}...")

# 调试信息
print(f"请求URL: {url}")
print(f"使用模型: {data['model']}")
print(f"图像路径: {image_path}, 遮罩路径: {mask_path}")

def main():
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"输入图像文件不存在: {image_path}")
        if not os.path.exists(mask_path):
            raise FileNotFoundError(f"遮罩图像文件不存在: {mask_path}")
            
        # 打开图像文件
        with open(image_path, 'rb') as image_file_handle, open(mask_path, 'rb') as mask_file_handle:
            files = {
                'image': ('image.png', image_file_handle, 'image/png'),
                'mask': ('mask.png', mask_file_handle, 'image/png')
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, files=files, data=data, timeout=300)  # 超时时间设置为5分钟
            
            # 解析响应
            try:
                response_data = response.json()
                print("API响应状态码:", response.status_code)
                print("API响应:", json.dumps(response_data, ensure_ascii=False)[:500] + "..." if len(json.dumps(response_data, ensure_ascii=False)) > 500 else json.dumps(response_data, ensure_ascii=False))
                
                # 处理成功响应
                if response.status_code == 200 and 'data' in response_data:
                    # 从响应中获取base64编码的图像
                    b64_image = response_data['data'][0]['b64_json']
                    
                    # 保存生成的图像
                    output_path = f"output_{os.path.basename(image_path)}"
                    with open(output_path, "wb") as f:
                        f.write(base64.b64decode(b64_image))
                    print(f"✅ 生成的图像已保存到: {output_path}")
                else:
                    print(f"⚠️ API返回了错误: {response_data.get('error', {}).get('message', '未知错误')}")
                    
            except ValueError as e:
                print(f"API响应不是有效的JSON格式: {response.text[:1000]}")
                print(f"JSON解析错误: {str(e)}")
                raise Exception(f"API响应格式错误: {response.text[:200]}")
    
    except FileNotFoundError as e:
        print(f"❌ 错误: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API请求错误: {str(e)}")
    except Exception as e:
        print(f"❌ 发生未知错误: {str(e)}")

if __name__ == "__main__":
    main()
    
"""
使用说明:
1. 确保已安装所需的依赖库: pip install requests python-dotenv
2. 在同目录下创建 .env 文件，并设置 OPENAI_API_KEY=your_api_key_here
3. 准备一个输入图像和一个遮罩图像(遮罩中白色区域表示要编辑的部分)
4. 运行命令示例:
   python test.py --image input.png --mask mask.png --prompt "将背景改为海滩场景" --size 1024x1024
   
遮罩说明:
- 遮罩中白色区域(RGB值接近255,255,255)表示要编辑的区域
- 遮罩中原有区域(RGB值接近0,0,0)表示要保留原图的区域
"""
